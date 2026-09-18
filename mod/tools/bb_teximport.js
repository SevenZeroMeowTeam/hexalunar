(function () {
var data = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAGP0lEQVR42u1Xv28dRRD+dm~v9rCtgGOcHySRICQCoZCSNMhVShoKCv4CKgr+BNpQgpAoaYAuSkMVCckVTRCR6AApKAIZGSWRY1nvbvd2KexvmHuJYz~LRIm8K1nP797c7Mw333yza86ceS0DQFVVyDkjhAAAyDnDWovl5ZNIKQEAYoxo2xYpJaSUkHPGnTu~AQDqukZKCTFGAIBzDs45XLnyLmKMqKoKMUY458TOGINbt35EzhlcdV1jGAbZ~4fvv0LOGcMwwDkHALDWIucMYww+~PpXeab36PseAPD+8QEpJVhrJQcAaJpmO86Ukjhm8nVdY3o55ySwnDNSSqjrGs45GGNGiTPAruvQdZ34pw9rrQTQNA1ijBiGQRJh8NZapJRgjBHQq6oCgJE9P40xEk9d1+j7Xp6FECRe59x~8Q7DgKqq0HUdvPfIOaPve9R1DWMMhmGQxKc377pOwGCwrDBZVFUVQggwxkiFAMB7j77vEWOELsIwDBK0Bs17L0AYY0bFYVH4PhmwzeqAEIIwVwNnrYWjcdu2GIYBMUY0TSM0JRB8gc~IAILCIJgg24q~M7i2baXCVVXBWvsIs8gKa62AzP1pwzgBCDumq51zHrUcAeWKMcIS~b7vxQmrQhqzomwRAsUVQhDE+Rs1hX7YswSQlUgpSXU1G8koUrxpmkfaLcaInDO898I0agBbYjKZCPO4B~PbKcB2BZqmkaCMMTDGwHsvzuiAzihMxphRe+gq8JM29MVEad91nfi21kr1yDDaMpmqqtA0jYBKXeH3lBJCCJIkW4hMYgFSSrBMloGyYqwgEXPOiT4450aqT7R1xXQFaUOmUFc0UNyLjCITCKiOgd8pamQD6U7AqqoSQee+jIkg2xDCKOEdYZAgST2dkB5TTJ4+yA7tj1Vzzo0qp5PRLaIT6bpOmEaQmTynB~dg8Qhq3~eYTCayL0FhIYwxMEtLJzNFjg6aphFqnjhxWqrN5Cl6xhi8+OJL6PteVFhXJ4SAD~7+Q4JnBbWOfIFG2o3TR2vIpUuXJXD+HkJA0zQIIeDW~W6k~qQ8GfX5Jx9JmzAG6t4wDHB6pHjvpdeMMQIEacmXSStdAVaM6sxW0XScTCbjQ4hz8JUX8aLqM8mqqqQ9ySrqBytLxuhxy9jIPOoJzxj6PGLrupZEKRzee+lZ3ducEnoa8Bl9aIXX4sRAWWG2jj5oMVD9yYCp3IyFrcpikGUEm6LKNpzWNmGlPoSwL5kU+2raOQ9BDIJjkpswGSbOpDUoPJQYb6Qy1ADuRWD1CVOzbjKZPBIf~RB4xqVPt5qtloFoimnBoXix2txQiyHnsz4V6rHEd3nMJuAShBLTpmnkfw0IWcBRSUAJOv1rVlAXGCttdZtbXUGKGTcn+nrkxBhH52oGo~uUQTMZBhpjRNd1QmsyQeuLBlePU~om0Dyj6CM3i6EFUd8hdJwcwZa00OOKPd51nVCRgejzt6YTgyNgZBYZoSubUpK5zDEbQhiBRQ3id4qfpjcZoUWae3O0Tp~~27YdTSzLxOlQC5r3XhCkY30D1G2jRZL3B3150bOeY5WB0BcTob+2bUfs0XTXV2h9p9B6QJZRg~SZY3SZ2u~f3NzCgZ~PzS081m4~z3bzf1B7bWcBYH7+GM6ePf~ET71OnXpV~vRaWjqNy5ffwdLSaTxpXbz4Ns6ffwt7rQsX9rbRa3n5Fcy65G64snIVALC6enNksLJyFTdufIfDXOvra6Pvc3MLe76zH5v19b9msh8BsLp6E~fv~4PFxZdHBtOAbFfwDfl~be3OzADMzy~A+xfw4MH6oYG634Snl9nph31vsrW1eaDnDHDabrfAt7Y25f1Zkvtp7SG+~eVPAMBnV9~cmwGzIreb~X79zLLf40Dda7338aezMeDatS8zANy+~fNML16~~s2uFd2NDc~iMjsj48Bra2sTx44dBwBsbNwTAM6dex0AcPfu7880AO4wnGxs3MPzutz~pb4PH24cDQB2WzGG5wIA+zQ2eVb7~6kBcCRbYHFxCQCwufmgtMCRZMCRnwKHedF57gB4llW~aEABoABQACgAFAAKAAWAAkABoABQACgAFAAKAAWAAkABoABQACgAFAAKAAWAAkABoABQACgAHMX1L1u82Y5b3IASAAAAAElFTkSuQmCC'.split('~').join('/');
Texture.all.slice().forEach(function (t) { if (t.remove) t.remove(); });
var tex = new Texture({ name: 'crossbow', width: 64, height: 64 });
tex.add();
tex.fromDataURL(data, { name: 'crossbow', width: 64, height: 64, particle: false });
tex.uv_width = 64;
tex.uv_height = 64;
tex.setAsDefaultTexture();
tex.apply();
Cube.all.forEach(function (c) { c.texture = 0; });
Canvas.updateAll();
if (typeof updateUVEditor === 'function') updateUVEditor();
var d = tex.ctx.getImageData(3, 3, 1, 1).data;
return JSON.stringify({
  canvas: tex.canvas.width + 'x' + tex.canvas.height,
  uv: tex.getUVWidth() + 'x' + tex.getUVHeight(),
  px_sample: [d[0], d[1], d[2], d[3]],
  default_tex: Texture.getDefault() ? Texture.getDefault().name : null,
  cubes: Cube.all.length
}, null, 1);
})();
