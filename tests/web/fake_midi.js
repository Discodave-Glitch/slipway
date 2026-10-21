// A simulated FM-1 on Web MIDI for browser tests (adapted from Felucca's test_web.mjs FakeFM1, GPL-3.0).
(() => {
  const HS = [0xF0,0,0x32,0x45,0,0,0,0x40,0x7F,0xF7], UP = [0xF0,0x22,0x24,0x35,0x7F,0xF7];
  const eq = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
  const pack7 = (data) => { const out = []; let acc = 0, nb = 0; for (const b of data) { acc |= b << nb; nb += 8; while (nb >= 7) { out.push(acc & 0x7F); acc >>>= 7; nb -= 7; } } if (nb) out.push(acc & 0x7F); return out; };
  const unpack7 = (s) => { const out = []; let acc = 0, nb = 0; for (const b of s) { acc |= (b & 0x7F) << nb; nb += 7; while (nb >= 8) { out.push(acc & 0xFF); acc >>>= 8; nb -= 8; } } return out; };
  const dev = window.__fake = { identity: "FM-1_015", name: "FM-1", image: new Uint8Array(0x4000), finalIdentity: "FM-1_900", served: 0, bad: 0, writes: 0, perm: sessionStorage.getItem("denyMidi") ? "denied" : "granted", unplugAfter: Infinity, access: null };
  const access = dev.access = { inputs: new Map(), outputs: new Map(), onstatechange: null };
  let queue = [], waiting = null;
  function boot(identity, name) {
    dev.identity = identity; dev.name = name; waiting = null; queue = [];
    for (const m of [access.inputs, access.outputs]) { for (const p of m.values()) p.state = "disconnected"; m.clear(); }
    const id = Math.random().toString(36).slice(2);
    const input = { id: "i" + id, name, state: "connected", onmidimessage: null, open: async () => {} };
    const output = { id: "o" + id, name, state: "connected", open: async () => {}, send: (d) => {
      if (output.state !== "connected") throw new Error("InvalidStateError");
      setTimeout(() => rx(Array.from(d)), 1); } };
    dev.input = input; dev.output = output;
    access.inputs.set(input.id, input); access.outputs.set(output.id, output);
    if (access.onstatechange) setTimeout(() => access.onstatechange({}), 5);
  }
  const tx = (b) => { const i = dev.input; setTimeout(() => { if (i.state === "connected" && i.onmidimessage) i.onmidimessage({ data: Uint8Array.from(b) }); }, 1); };
  function next() {
    const r = queue.shift(); if (!r) return; waiting = r; const [addr, len] = r;
    const u = [0,0x59,0x30,0,0,0,0, addr & 0xFF, (addr >>> 8) & 0xFF, (addr >>> 16) & 0xFF, (addr >>> 24) & 0xFF, len & 0xFF, len >> 8, 0];
    let s = 0; for (let i = 6; i < 14; i++) s += u[i]; u.push(~s & 0xFF);
    tx([0xF0, ...pack7(u), 0xF7]);
  }
  function rx(d) {
    if (eq(d, HS)) {
      const t = [...new TextEncoder().encode(dev.identity)];
      tx([0xF0, ...pack7([0,0x59,0x11,0,0,0, ...t, ...new Array(28 - t.length).fill(0)]), 0xF7]);
    } else if (eq(d, UP)) {
      queue = dev.identity.startsWith("ota-")
        ? [...Array.from({ length: 6 }, (_, k) => [k * 512, 512]), [0xF0000000, 8]]
        : [[0, 64], [0x40, 160], [0x1000, 512], [0xE0000000, 8]];
      if (dev.identity.startsWith("ota-")) dev.writes++;
      next();
    } else if (waiting) {
      const u = unpack7(d.slice(1, -1)); const [addr, len] = waiting;
      const got = u.slice(14, 14 + (addr >= 0xE0000000 ? 8 : len));
      const want = addr >= 0xE0000000 ? [...new TextEncoder().encode("success"), 0] : Array.from(dev.image.subarray(addr, addr + len));
      if (!eq(got, want)) dev.bad++;
      waiting = null; dev.served++;
      if (dev.served >= dev.unplugAfter) { dev.input.state = dev.output.state = "disconnected"; return; }
      if (addr === 0xE0000000) setTimeout(() => boot("ota-" + dev.finalIdentity, "Felucca Update"), 300);
      else if (addr === 0xF0000000) setTimeout(() => boot(dev.finalIdentity, "FM-1"), 300);
      else next();
    }
  }
  dev.boot = boot;
  navigator.requestMIDIAccess = async () => { if (dev.perm !== "granted") throw new Error("denied"); return access; };
  boot("FM-1_015", "FM-1");
})();
