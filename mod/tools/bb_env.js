(function () {
var out = {};
out.require = typeof require;
out.process = typeof process;
out.is_desktop = !!window.isElectron || (typeof process !== 'undefined' && !!process.versions && !!process.versions.electron);
try {
  out.versions = (typeof process !== 'undefined' && process.versions) ? process.versions.electron : null;
} catch (e) { out.versions = 'ERR ' + e.message; }
try {
  var fs = require('fs');
  out.fs_read = typeof fs.readFileSync;
  out.cwd = process.cwd();
} catch (e) { out.fs_err = e.message; }
try {
  out.paths = {
    project: Project ? Project.save_path : null,
    bb_dir: (typeof Blockbench !== 'undefined' && Blockbench.user_data_path) ? Blockbench.user_data_path : null
  };
} catch (e) { out.paths_err = e.message; }
return JSON.stringify(out, null, 1);
})();
