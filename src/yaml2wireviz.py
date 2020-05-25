import yaml
import wireviz

filename = 'example1.yml'

with open(filename, 'r') as stream:
    try:
        input = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# print(input)

sections = ('options','nodes','wires')

for s in sections:
    print(s + ':')
    for k in input[s]:
        print(k + ': ', end='')
        print(input[s][k])
    print()

print('connections:')
for s in input['connections']:
    print(s)
print()

h = wireviz.Harness()
for k in input['nodes']:
    n = input['nodes'][k]
    h.add_node(k, type=n['type'], gender=n['gender'], pinout=n['pinout'])

for k in input['wires']:
    c = input['wires'][k]
    h.add_cable(k, mm2=c['mm2'], length=c['length'], num_wires=c['num_wires'], color_code=c['color_code'], shield=c['shield'])

for o in input['connections']:
    c1 = o['items'][0]
    w  = o['items'][1]
    c2 = o['items'][2]
    h.connect(w,c1,o[c1],o[w],c2,o[c2])

h.output(filename='output', format=('png',), view=False)
