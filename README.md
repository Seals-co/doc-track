# doc-track

doc-track is a tool that allows developpers to make CI fail when a piece of code marked as "is documented" is added / modified / deleted.

# Installation

# options available
`--version-from` # Git version of comparison used

`--version-to` # Git version to compare the first version to

`--path` # Path where comparison is checked

`--tags` # Pair list of start / end tag: `... --tags "# start","# end" "#start","#end"...`

`--config` # to specify config file, default .doctrack.yml

`--fail-status` # Return code in case code documented is modified, default 0

`--show-result` # To enable showing result in error output, default True

`--skip-blank-lines` # To skip blank lines changes of documented code, default True

# Mark code as documented

To mark code as documented, wrap it with both start tag and end tag.

Tag must be the only text on the line:
```python
class A:
    # documented
    def fct():
        return 22
    # end-documented
```
End tag must be different from start tag
