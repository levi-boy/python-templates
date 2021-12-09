import requests
import random
import time
import json
import sys
import re

from itertools import (
    chain, starmap,)


def err(error_test, close=True):
    input(error_test)
    if close:
        sys.exit()


def unit_time(unix_type='int'):
    if unix_type == 'int':
        return int(time.time())
    elif unix_type == 'float':
        return time.time()
    else:
        raise ValueError("unix_type must be 'int' or 'float'")


def read_json(file_name):
    error_text = f'some error while reading the file {file_name}'
    try:
        with open(file_name, 'rb') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        err(f"file {file_name} not found")
    except json.decoder.JSONDecodeError:
        try:
            with open(file_name, 'rb') as f:
                data = f.read().decode().replace(' ', '') \
                    .replace('\r', '').replace('\n', '')
                data = re.sub(r',}', '}', data)
                return json.loads(data)
        except json.decoder.JSONDecodeError:
            try:
                with open(file_name, 'r', encoding='utf-8-sig') as f:
                    data = f.read().replace(' ', '') \
                        .replace('\r', '').replace('\n', '')
                    data = re.sub(r',}', '}', data)
                    return json.loads(data)
            except Exception:
                err(error_text)
        except Exception:
            err(error_text)
    except Exception:
        err(error_text)


def write_to_json(filename, data, mode='w', indent=2, ensure_ascii=False):
    with open(filename, mode, encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def write_to_file(filename, data, mode='w'):
    with open(filename, mode, encoding='utf-8') as f:
        f.write(str(data))


def read_file(file_name):
    try:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                return f.read().splitlines()
        except UnicodeDecodeError as e:
            with open(file_name, 'r') as f:
                return f.read().splitlines()
        except Exception as e:
            with open(file_name, 'r', encoding='ISO-8859-1') as f:
                return f.read().splitlines()
    except Exception as e:
        err(f'file {file_name} unreadable', close=False)


def net_to_cookie(filename, service):
    cookies = {}
    file_data = read_file(filename)
    if file_data is None:
        return
    for line in file_data:
        try:
            if not re.match(r'^\#', line) and service in line:
                line_fields = line.strip().split('\t')
                cookies[line_fields[5]] = line_fields[6]
        except Exception as e:
            continue

    return cookies


def format_json(dictionary):
    def unpack(parent_key, parent_value):
        if isinstance(parent_value, dict):
            for key, value in parent_value.items():
                temp1 = parent_key + '_' + key
                yield temp1, value
        elif isinstance(parent_value, list):
            i = 0
            for value in parent_value:
                temp2 = parent_key + '_' + str(i)
                i += 1
                yield temp2, value
        else:
            yield parent_key, parent_value

    while True:
        dictionary = dict(chain.from_iterable(
            starmap(unpack, dictionary.items())))
        if not any(isinstance(value, dict) for value in dictionary.values()) and \
                not any(isinstance(value, list) for value in dictionary.values()):
            break

    return dictionary


def get_random_proxy(proxies, proxy_type):
    random_proxy = random.choice(proxies)
    try:
        ip, port, username, password = random_proxy.split(':')
        return {'https': f'{proxy_type}://{username}:{password}@{ip}:{port}'}
    except ValueError:
        return {'https': f'{proxy_type}://{random_proxy}'}


def connection(obj, url, status_code, proxies=None, proxy_type=None,
               connection_counter=25, logs=False, **kwargs):
    while connection_counter > 0:
        if proxies and proxy_type:
            random_proxy = get_random_proxy(proxies, proxy_type)
            kwargs.update(proxies=random_proxy)
        try:
            r = obj(url, **kwargs)
            if r.status_code in status_code:
                return r
            connection_counter -= 1
        except requests.RequestException as e:
            if logs:
                print(e)
        connection_counter -= 1
