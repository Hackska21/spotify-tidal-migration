import json
import os
import pickle


def dump_to_file(file_name, data):
    with open(file_name, '+w') as outfile:
        json.dump(data, outfile)


def dump_to_pickle(file_name, data, path=''):
    create_folder(path) if path != '' else None
    with open(f'{path}{file_name}.pickle', 'wb') as outfile:
        pickle.dump(data, outfile)


def load_from_pickle(file_name, path=''):
    file = f'{path}{file_name}.pickle'
    if not os.path.exists(file):
        return None
    with open(file, 'rb') as f:
        data = pickle.load(f)
    return data


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
