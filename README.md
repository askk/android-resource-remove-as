# android-resource-remove-as
android unused resource remove for android studio base on android-resource-remove

How to:

step 1:   inspect code for your application or module, export result to directory after analyze 

step 2:   python resource-clean.py --xml /Users/xxxx/xxx/AndroidLintUnusedResources.xml --app your_code_directory

NOTE:   your_code_directory is your code directory, the parent directory of "src"
