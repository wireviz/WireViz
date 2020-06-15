import wireviz
import os

readme = '../examples/readme.md'
readme = os.path.abspath(readme)

do_demos = False
do_examples = True
do_tutorial = True

if do_demos:
    for i in range(1,3):
        fn = '../examples/demo{:02d}.yml'.format(i)
        print(fn)
        wireviz.parse(fn, gen_bom=True)

if do_examples:
    with open(readme, 'w') as file:
        file.write('# Example gallery\n')
        for i in range(1,7):
            fn = '../examples/ex{:02d}.yml'.format(i)
            print(fn)
            wireviz.parse(fn, gen_bom=True)

            file.write('## Example {:02d}\n'.format(i))
            file.write('![](ex{:02d}.png)\n\n'.format(i))
            file.write('[Source](ex{:02d}.yml) - [Bill of Materials](ex{:02d}.bom.tsv)\n\n\n'.format(i,i))

if do_tutorial:
    for i in range(1,7):
        fn = '../tutorial/tutorial{:02d}.yml'.format(i)
        print(fn)
        wireviz.parse(fn, gen_bom=True)
