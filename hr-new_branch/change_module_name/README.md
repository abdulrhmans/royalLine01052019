Odoo - Rename an addon without losing data
==========================================

Rename addon
------------

- Change ```__manifest__.py``` addon name field
- Change ```README.rst``` file



- Change translations files (i18n folder, .po and .pot files)

```bash
cd i18n
mv '<old_name>.pot' '<new_name>.pot'
sed -i 's/#\(.*\)\* <old_name>/#\1* <new_name>/g' *.po*
sed -i 's/#\. module: <old_name>/#. module: <new_name>/g' *.po*
sed -i 's/#: view:\(.*\):<old_name>/#: view:\1:<new_name>/g' *.po*
sed -i 's/#: model:\(.*\),name:<old_name>/#: model:\1,name:<new_name>/g' *.po*
sed -i 's/#: code:\(.*\)\/<old_name>\//#: code:\1\/<new_name>\//g' *.po*
```

- Change XML ID (module part) on views, templates, records, ...

Execute these SQL queries
-------------------------

```sql
UPDATE ir_module_module SET name = '<new_name>' WHERE name = '<old_name>';
UPDATE ir_model_data SET module = '<new_name>' WHERE module = '<old_name>';
UPDATE ir_model_data SET name = 'module_<new_name>' 
       WHERE name = 'module_<old_name>' 
       AND module = 'base' 
       AND model = 'ir.module.module';
UPDATE ir_module_module_dependency SET name = '<new_name>'
       WHERE name = '<old_name>';
UPDATE ir_translation SET module = '<new_name>'
       WHERE module = '<old_name>';
```

Update any addon that depends on this one
-----------------------------------------

- Change ```__manifest__.py``` addon depends field



Update the .PYs and .XMLs files that contain the old name of medule
-----------------------------------------------------------




Restart Odoo
------------

References
----------
https://gist.github.com/antespi/38978614e522b1a99563




