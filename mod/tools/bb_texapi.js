(function () {
var out = {};
out.proto = Object.getOwnPropertyNames(Texture.prototype);
out.group_proto = Object.getOwnPropertyNames(Group.prototype);
out.project_res = [Project.texture_width, Project.texture_height];
try {
  var t = new Texture({ name: 'probe64', width: 64, height: 64 });
  t.add();
  out.created = { w: t.width, h: t.height, cw: t.canvas ? t.canvas.width : null, ch: t.canvas ? t.canvas.height : null };
  t.width = 64; t.height = 64;
  out.after_set = { w: t.width, h: t.height, cw: t.canvas ? t.canvas.width : null };
  out.proj_after = [Project.texture_width, Project.texture_height];
  t.remove();
} catch (e) { out.err = e.message; }
return JSON.stringify(out, null, 1);
})();
