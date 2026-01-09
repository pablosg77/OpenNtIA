#!/usr/bin/env python3
# filepath: /home/ubuntu/openntIA/collector/data/pfe_exceptions.py
from lxml import etree
import re
from datetime import datetime
import time
from jnpr.junos import Device
from jnpr.junos.exception import ConnectAuthError, RpcError
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Función para leer credenciales
def read_credentials(file_path):
    with open(file_path, 'r') as credentials:
        return yaml.safe_load(credentials)

# Función para leer archivo YAML de routers
def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def normalize_exception(exc_type: str) -> str:
    """Normaliza el nombre de la excepción para usarlo como tag"""
    exc = exc_type.lower().strip()
    exc = exc.replace("exceptions", "")
    exc = exc.replace("exception", "")
    exc = exc.strip()
    exc = re.sub(r"\s+", "_", exc)
    return exc

def safe_xpath_text(element, xpath_expr):
    """Extrae texto de forma segura desde un xpath"""
    try:
        result = element.xpath(xpath_expr)
        if result is None:
            return ""
        if isinstance(result, list):
            # Convertir cada elemento a string y filtrar None/vacíos
            texts = [str(x) for x in result if x is not None]
            return ''.join(texts)
        return str(result)
    except Exception as e:
        print(f"Error en xpath '{xpath_expr}': {e}")
        return ""

# Recolector de excepciones PFE
def get_pfe_exception(i):
    regex = r"(.*\w+\s+)DISC\(.*\)\s+(\d+\s)(.*)"
    dt_string = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    my_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    cred = read_credentials('credentials.yaml')
    
    try:
        with Device(host=i, user=cred[0]['username'], password=cred[0]['password'], port=22) as dev:
            # Recolectar tarjetas AFT y FPC
            fpcs_aft = dev.rpc.get_chassis_inventory()
            aft_slots = fpcs_aft.xpath("//chassis/chassis-module[contains(./description,'MPC1')]/name//text()")
            
            # Convertir aft_slots a lista si no lo es
            if aft_slots is None:
                aft_slots = []
            elif not isinstance(aft_slots, list):
                aft_slots = [aft_slots]
            
            aft_slot = ''.join([str(s) for s in aft_slots]).split()[1] if aft_slots and len(aft_slots) <= 1 else None
            aft_list = [str(slot).split(' ')[-1] for slot in aft_slots if len(aft_slots) > 1]

            fpc_list = dev.rpc.get_fpc_information().xpath('//fpc[state="Online"]//slot//text()')
            if fpc_list is None:
                fpc_list = []
            
            # Procesar excepciones para cada FPC
            for f in fpc_list:
                f = str(f)  # Asegurarse de que f es un string
                if f != aft_slot:
                    o_result = dev.rpc.cli(f"show pfe statistics exceptions fpc {f}")
                    
                    # Usar la función segura para extraer texto
                    slots_data = safe_xpath_text(o_result, "//output//text()")
                    
                    if not slots_data:
                        continue
                    
                    for exc_type, value, _ in re.findall(regex, slots_data):
                        if value.strip() != "0":
                            exception = normalize_exception(exc_type)
                            my_dict[i][f][dt_string][exc_type.strip()] = value.strip()
                else:
                    # Si es tarjeta AFT, recolectar datos para uno o más AFT
                    target_fpcs = [aft_slot] if aft_slot else aft_list
                    for target_fpc in target_fpcs:
                        fpc_target = "fpc" + str(target_fpc)
                        try:
                            aft_excep = dev.rpc.request_pfe_execute(target=fpc_target, command="show jnh exceptions level terse inst 0")
                            
                            # Usar la función segura para extraer texto
                            aft_data = safe_xpath_text(aft_excep, "//output//text()")
                            
                            if not aft_data:
                                continue
                            
                            for exc_type, value, _ in re.findall(regex, aft_data):
                                if value.strip() != "0":
                                    exception = normalize_exception(exc_type)
                                    my_dict[i][target_fpc][dt_string][exc_type.strip()] = value.strip()
                        except RpcError as rpc_err:
                            print(f"Error ejecutando RPC en {fpc_target}: {rpc_err}")

    except ConnectAuthError as auth_err:
        print(f"Error de autenticación en {i}: {auth_err}")
        return []  # Si falla la autenticación, devuelve una lista vacía
    except Exception as e:
        print(f"Error general en {i}: {e}")
        return []

    # Procesar `my_dict` en formato para InfluxDB
    lines = []
    for f, timestamps in my_dict[i].items():
        for timestamp, stats in timestamps.items():
            timestamp_ns = int(datetime.strptime(timestamp, '%d-%m-%Y %H:%M:%S').timestamp() * 1e9)
            for exc_type, value in stats.items():
                exception = normalize_exception(exc_type)
                line = (
                    f"pfe,"
                    f"device={i},"
                    f"slot={f},"
                    f"exception={exception} "
                    f"count={value} "
                    f"{timestamp_ns}"
                )
                lines.append(line)
                
    return lines

# Ejecución concurrente
def main():
    routers = read_yaml('routers.yaml')

    with ThreadPoolExecutor(max_workers=7) as executor:
        future_to_device = {executor.submit(get_pfe_exception, i['hostname']): i['hostname'] for i in routers}
        for future in as_completed(future_to_device):
            hostname = future_to_device[future]
            try:
                datapoints = future.result()
                if datapoints:
                    print('\n'.join(datapoints))
            except Exception as exc:
                print(f"{hostname} generó una excepción: {exc}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main()
