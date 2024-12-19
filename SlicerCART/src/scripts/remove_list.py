import yaml

filepath = '/Users/maximebouthillier/gitmax/data_confid/test_bidon/remaining_list.yaml'


with open(filepath, 'r') as file:
    elements = yaml.safe_load(file)['CASES']

print('before', elements)

elements.remove(elements[0])

elements = {'CASES': elements}

with open(filepath, 'w') as file:
    yaml.dump(elements, file)

print('after', elements)
