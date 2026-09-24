import unreal

unreal.log("ASSET_TOOLS_HELPERS=%s" % dir(unreal.AssetToolsHelpers))
tools = unreal.AssetToolsHelpers.get_asset_tools()
unreal.log("ASSET_TOOLS=%s" % dir(tools))
for name in ("AssetRenameData", "AssetTools", "EditorAssetLibrary"):
    obj = getattr(unreal, name, None)
    unreal.log("ASSET_API_%s=%s" % (name, dir(obj) if obj else None))
    if obj:
        for method in ("rename_assets", "rename_asset", "rename_loaded_asset"):
            value = getattr(obj, method, None)
            if value:
                unreal.log("ASSET_API_METHOD_%s_%s=%s" % (name, method, value))

for owner, method in ((tools, "rename"), (tools, "rename_assets"),
                      (unreal.EditorAssetLibrary, "rename_asset"),
                      (unreal.EditorAssetLibrary, "rename_loaded_asset")):
    value = getattr(owner, method)
    unreal.log("ASSET_API_DOC_%s=%s" % (method, getattr(value, "__doc__", None)))

data = unreal.AssetRenameData()
unreal.log("ASSET_RENAME_DATA_DOC=%s" % unreal.AssetRenameData.__doc__)
unreal.log("ASSET_RENAME_DATA_TEXT=%s" % data.export_text())
for prop in ("bOnlyFixSoftReferences", "bCreateRedirector", "OldObjectPath", "NewObjectPath"):
    try:
        unreal.log("ASSET_RENAME_DATA_PROP_%s=%s" % (prop, data.get_editor_property(prop)))
    except Exception as exc:
        unreal.log("ASSET_RENAME_DATA_PROP_%s_ERROR=%s" % (prop, exc))

for args in ((None, "/Game/Test", "Test"),
             (None, "/Game/Test", "Test", None, None, True),
             (None, "/Game/Test", "Test", None, None, True, False)):
    try:
        candidate = unreal.AssetRenameData(*args)
        unreal.log("ASSET_RENAME_DATA_ARGS_%d=%s" % (len(args), candidate.export_text()))
    except Exception as exc:
        unreal.log("ASSET_RENAME_DATA_ARGS_%d_ERROR=%s" % (len(args), exc))

for setter in ("set_editor_property", "assign"):
    try:
        if setter == "set_editor_property":
            data.set_editor_property("bOnlyFixSoftReferences", True)
        else:
            data.assign(None, "/Game/Test", "Test")
        unreal.log("ASSET_RENAME_DATA_SET_%s=%s" % (setter, data.export_text()))
    except Exception as exc:
        unreal.log("ASSET_RENAME_DATA_SET_%s_ERROR=%s" % (setter, exc))

try:
    imported = unreal.AssetRenameData(None, "/Game/Test", "Test")
    before = imported.export_text()
    imported.import_text(before.replace("bOnlyFixSoftReferences=False", "bOnlyFixSoftReferences=True"))
    unreal.log("ASSET_RENAME_DATA_IMPORT=%s" % imported.export_text())
except Exception as exc:
    unreal.log("ASSET_RENAME_DATA_IMPORT_ERROR=%s" % exc)
unreal.log("PACKAGE_FUNCS=%s" % [x for x in dir(unreal) if "package" in x.lower()])
unreal.log("OBJECT_RENAME_DOC=%s" % unreal.Object.rename.__doc__)
for fn in (unreal.find_package, unreal.load_package, unreal.new_object):
    unreal.log("PACKAGE_FN_%s=%s" % (fn.__name__, fn.__doc__))
for cls in (unreal.Package, unreal.PackageTools, unreal.PackageFactory):
    unreal.log("PACKAGE_API_%s=%s" % (cls.__name__, dir(cls)))
    for method in dir(cls):
        value = getattr(cls, method, None)
        if callable(value) and not method.startswith("_"):
            doc = getattr(value, "__doc__", None)
            if doc:
                unreal.log("PACKAGE_API_DOC_%s_%s=%s" % (cls.__name__, method, doc))
