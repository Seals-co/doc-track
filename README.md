# doc-track

doc-track is a tool that allows developpers to make CI fail or add message to commit / merge requests when a piece of code marked as "is documented" is added / modified / deleted.
# options available
--lang              # to configure language used, will automatically set tags

--add-git-message   # to add message to git commits and merge request

--fail-status       # to set $? to the specified value when fail


# tagging a line
tagging a line to flag it has documented add a comment in the same line wit flag word