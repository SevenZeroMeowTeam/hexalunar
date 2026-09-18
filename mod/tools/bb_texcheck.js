(function () {
var out = {};
out.res = [Project.texture_width, Project.texture_height];
out.tex_count = Texture.all.length;
var t = Texture.all[0];
if (t) {
  out.canvas = t.canvas ? (t.canvas.width + 'x' + t.canvas.height) : null;
  out.uv = t.getUVWidth() + 'x' + t.getUVHeight();
  try {
    var a = t.ctx.getImageData(3, 3, 1, 1).data;
    var b = t.ctx.getImageData(28, 18, 1, 1).data;
    var c = t.ctx.getImageData(50, 16, 1, 1).data;
    out.px = { body: [a[0], a[1], a[2], a[3]], mag: [b[0], b[1], b[2], b[3]], cam: [c[0], c[1], c[2], c[3]] };
  } catch (e) { out.px_err = e.message; }
}
out.cubes = Cube.all.length;
out.groups = Group.all.length;
return JSON.stringify(out, null, 1);
})();
