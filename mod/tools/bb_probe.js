(function () {
var info = {};
info.bb = Blockbench.version;
info.format = Project.format.id;
info.name = Project.name;
info.res = [Project.texture_width, Project.texture_height];
info.box_uv = Project.box_uv;
info.tex = Texture.all.map(function (t) { return t.name + ' ' + t.width + 'x' + t.height; });
info.has_cube = typeof Cube;
info.has_group = typeof Group;
info.has_anim = typeof Animation;
info.anims = (Project.animations || []).map(function (a) { return a.name; });
info.groups = Group.all.map(function (g) { return g.name; });
info.cubes = Cube.all.length;
info.props = Object.keys(Project).filter(function (k) {
  return /gecko|display|anim/i.test(k);
});
info.fmt_props = Object.keys(Project.format).filter(function (k) {
  return /gecko|anim|display/i.test(k);
});
info.single_texture = Project.format.single_texture;
info.bone_rig = Project.format.bone_rig;
info.anim_mode = Project.format.animation_mode;
return JSON.stringify(info, null, 1);
})();
