# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import time
import random
import threading
import subprocess
from datetime import datetime
from itertools import chain, starmap

import requests


""" Critical errors
    12 - error in check_user()
    133 - error in check_uuid()
    122 - error in get_uuids_from_html()
"""


def close_with_message(e: str):
    input(e)
    sys.exit()
    
    
def error_with_timeout(e: str, timeout=3):
    print(e)
    time.sleep(timeout)


def get_json_from_file(file_name):
    error_text = f'Some error while reading the file {file_name}'
    try:
        with open(file_name, 'rb') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        close_with_message(f"File {file_name} not found.")
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
                close_with_message(error_text)
        except Exception:
            close_with_message(error_text)
    except Exception:
        close_with_message(error_text)


def unix_time():
    return int(time.time())


def get_random_proxy(proxies, proxy_type):
    random_proxy = random.choice(proxies)
    try:
        ip, port, username, password = random_proxy.split(':')
        return {'https': f'{proxy_type}://{username}:{password}@{ip}:{port}'}
    except ValueError:
        return {'https': f'{proxy_type}://{random_proxy}'}


def connection(obj, url, proxies, proxy_type='http', **kwargs):
    connection_counter = 25
    while connection_counter:
        if proxies:
            proxy = get_random_proxy(proxies, proxy_type)
            kwargs.update(proxies=proxy)
        try:
            return obj(url, **kwargs)
        except requests.RequestException:
            pass
        connection_counter -= 1


def threading_pool(condition, thread_count, func, args):
    while condition:
        while threading.active_count() <= thread_count:
            threading.Thread(target=func, args=args, daemon=False).start()


def check_uuid():
    try:
        uuid_data = subprocess.check_output("wmic csproduct get uuid").decode()
        try:
            return uuid_data.split('\n')[1][:36].lower()
        except:
            close_with_message('uuid not found')
    except:
        close_with_message('Critical error 133.')


def get_uuids_from_html(text: str):
    try:
        i = 1
        start = '" class="blob-code blob-code-inner js-file-line">'
        end = '</td>'
        uuids_list = []
        while True:
            try:
                uuid = text.split(start)[i].split(end)[0]
                uuids_list.append(uuid.strip().replace(',', ''))
            except IndexError:
                break
            i += 1
        return uuids_list
    except:
        close_with_message('Critical error 122.')


def check_user(check_link, no_license_text, license_expired_text):
    try:
        r = connection(requests.get, check_link)
        if not r:
            close_with_message('Critical error 12.')
        uuids = get_uuids_from_html(text=r.text)
        current_uuid = check_uuid()
        current_unix_time = unix_time()
        for uuid in uuids:
            if current_uuid in uuid:
                splitted_uuid = uuid.split('_')
                user_uuid = splitted_uuid[0]
                uuid_time = splitted_uuid[1]
                if current_unix_time > int(uuid_time):
                    close_with_message(license_expired_text)
                date = datetime.fromtimestamp(int(uuid_time))
                print("The license is valid until:", date)
                print('Success!')
                return
        close_with_message(no_license_text)
    except:
        close_with_message('Critical error 12.')


# check_user(check_link='https://github.com/levi-boy/holop/blob/master/test.txt',
#            no_license_text='No license. Telegram: @telemele', 
#            license_expired_text='License expired. Telegram: @telemele')


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


def cookies_finder(dir_name="data"):
    if not os.path.exists(dir_name):
        close_with_message("folder data not found")
    cookies = []
    for root, _, files in os.walk(dir_name):
        if files:
            for file in files:
                if "cook" in file and ".txt" in file:
                    cookie = os.path.join(root, file)
                    cookies.append(cookie)
    return cookies


def net_to_cookie(filename: str, service: str):
    cookies = {}
    try:
        with open(filename, 'r', encoding='utf-8') as fp:
            for line in fp:
                try:
                    if not re.match(r'^\#', line) and service in line:
                        lineFields = line.strip().split('\t')
                        cookies[lineFields[5]] = lineFields[6]
                except:
                    continue
    except UnicodeDecodeError:
        with open(filename, 'r') as fp:
            for line in fp:
                try:
                    if not re.match(r'^\#', line) and service in line:
                        lineFields = line.strip().split('\t')
                        cookies[lineFields[5]] = lineFields[6]
                except:
                    continue
    return cookies


def read_json(filename, mode='r'):
    if not os.path.exists(filename): return
    try:
        with open(filename, mode, encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(filename, mode) as f:
            return json.load(f)


def write_to_json(filename, data, mode='w', indent=2, ensure_ascii=False):
    with open(filename, mode, encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def write_to_file(filename, data, mode='a'):
    with open(filename, mode, encoding='utf-8') as f:
        f.write(str(data))


def read_file(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as fp:
            return fp.read().splitlines()
    except UnicodeDecodeError as e:
        try:
            with open(file_name, 'r') as fp:
                return fp.read().splitlines()
        except Exception as e:
            try:
                with open(file_name, 'r', encoding='ISO-8859-1') as fp:
                    return fp.read().splitlines()
            except Exception as e:
                pass
    except Exception as e:
        pass
