import omni.ext
import omni.ui as ui
import omni.usd

from pxr import UsdGeom, Sdf
import carb


# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[siborg.utils.reparent] some_public_function was called with x: ", x)
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class SiborgUtilsReparentExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[siborg.utils.reparent] siborg utils reparent startup")

        self._window = ui.Window("My Window", width=300, height=300)

        self._prim_paths = []

        with self._window.frame:
            with ui.VStack():
                label = ui.Label("Select prim(s) to copy")

                def on_copy():
                    usd_context = omni.usd.get_context()

                    if (selection := usd_context.get_selection()) is not None:
                        self._prim_paths = selection.get_selected_prim_paths()
                        label.text = f"{self._prim_paths} copied"
                    else:
                        carb.log_error("No prims selected")
                        return

                def on_paste():
                    usd_context = omni.usd.get_context()
                    selection = usd_context.get_selection()
                    xform_cache = UsdGeom.XformCache()

                    if len(path := selection.get_selected_prim_paths()) == 1:
                        path = Sdf.Path(path[0])
                        stage = usd_context.get_stage()
                        for prim_path in self._prim_paths:

                            new_path = path.AppendChild(Sdf.Path(prim_path).name)
                            omni.usd.duplicate_prim(stage, prim_path, new_path)

                            old_prim = stage.GetPrimAtPath(prim_path)
                            old_prim_world = xform_cache.GetLocalToWorldTransform(old_prim)

                            new_prim = stage.GetPrimAtPath(new_path)
                            parent = new_prim.GetParent()
                            parent_xform_inv = xform_cache.GetLocalToWorldTransform(parent).GetInverse()
                            
                            xformable = UsdGeom.Xformable(new_prim)
                            xformable.SetXformOpOrder([])
                            xform_op = xformable.AddTransformOp()
                            xform_op.Set(parent_xform_inv * old_prim_world)

                            label.text = f"Pasted {len(self._prim_paths)} prims"

                    else:
                        label.text = "Select one parent prim to paste into"
                        return


                with ui.HStack():
                    ui.Button("Copy Prim", clicked_fn=on_copy)
                    ui.Button("Paste Prim", clicked_fn=on_paste)

    def on_shutdown(self):
        print("[siborg.utils.reparent] siborg utils reparent shutdown")
