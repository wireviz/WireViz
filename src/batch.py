import wireviz

# TODO: make examples (progressively more complex), batch process all of them
for i in range(1,3):
    fn = '../examples/demo{:02d}.yml'.format(i)
    print(fn)
    wireviz.parse(fn)
for i in range(1,5):
    fn = '../examples/ex{:02d}.yml'.format(i)
    print(fn)
    wireviz.parse(fn)
