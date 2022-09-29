import yaml


def parse_yaml(config):
    with open(config, "r") as stream:
        try:
            ret_dict = yaml.load(stream, Loader=yaml.Loader)
        except yaml.YAMLError as exc:
            print(exc)
    return ret_dict
