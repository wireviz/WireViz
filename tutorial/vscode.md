## Editing y(a)ml files with VSCode

If you already use vscode as your editor you are in luck. Steffano wrote a very handy how-to setup run-on-save extesion for vscode.

https://www.stefanocottafavi.com/vscode_wireviz/


If you want to use the prepend parameter so you can use a parent document (components.yml) with all your components defined you could do the following.

```yaml
"settings": {
    "emeraldwalk.runonsave": {
        "commands": [
            {
                "match": "\\.yml$",
                "cmd": "wireviz --prepend  components.yml ${file} -f h"
            },
            
        ]
    }
}
```

(the -f h instructs wireviz to only produce a html file. Do a wireviz -h for a overview of all the parameters)