from kivy.core.image import Image as CoreImage


class SpriteAnim:
    def __init__(self):
        self.sheets = {}
        self.state = None
        self.frame = 0.0
        self.loop = True
        self.flip_x = False
        self._tex = None
        self._rects = []
        self._fps = 0.0
        self._frame_durations = None
        self._frame_meta = None

    def add_sheet_by_count(
        self,
        state,
        filepath,
        frame_count,
        frame_h=None,
        fps=6,
        row_y_px=0,
        frame_w=None,
        frame_step=None,
        start_x=0,
        frame_xs=None,
        frame_ws=None,
    ):
        img = CoreImage(filepath)
        tex = img.texture
        try:
            tex.mag_filter = 'nearest'
            tex.min_filter = 'nearest'
            tex.wrap = 'clamp_to_edge'  # avoid bleeding from neighboring frames
        except Exception:
            # Filters/wrap might not be available depending on platform
            pass

        W, H = tex.size
        # Auto-detect frame height if not provided; clamp to texture bounds otherwise
        if frame_h is None or frame_h <= 0:
            frame_h = H - row_y_px
        frame_h = max(1, min(frame_h, H - row_y_px))

        rects = []
        if frame_xs is not None:
            # Use explicit x positions (and optional per-frame widths)
            for i in range(min(frame_count, len(frame_xs))):
                sx = int(frame_xs[i])
                w = frame_w if frame_ws is None or i >= len(frame_ws) else frame_ws[i]
                if w is None or w <= 0:
                    w = frame_w
                if w is None or w <= 0:
                    # Fallback to evenly splitting remaining width
                    w = max(1, (W - sx) // max(1, frame_count - i))
                w = max(1, min(w, W - sx))
                rects.append((sx, row_y_px, w, frame_h))
        elif frame_w is not None and frame_w > 0:
            step = frame_step if frame_step is not None else frame_w
            for i in range(frame_count):
                sx = int(round(start_x + i * step))
                if sx >= W:
                    break
                w = max(1, min(frame_w, W - sx))
                rects.append((sx, row_y_px, w, frame_h))
        else:
            starts = [round(start_x + i * W / float(frame_count)) for i in range(frame_count)]
            for i, sx in enumerate(starts):
                ex = round(start_x + (i + 1) * W / float(frame_count))
                w = max(1, min(W - sx, ex - sx))
                rects.append((sx, row_y_px, w, frame_h))

        self.sheets[state] = {"tex": tex, "rects": rects, "fps": float(fps)}

    def add_sheet_from_frames(self, state, filepath, frames, fps=6, frame_durations=None):
        """
        Add an animation using explicit frame rects.
        frames: list of dicts with x,y,w,h
        frame_durations: optional list of per-frame durations (seconds); overrides fps when provided.
        """
        img = CoreImage(filepath)
        tex = img.texture
        try:
            tex.mag_filter = "nearest"
            tex.min_filter = "nearest"
            tex.wrap = "clamp_to_edge"
        except Exception:
            pass

        rects = []
        metas = []
        for f in frames:
            rects.append((int(f["x"]), int(f["y"]), int(f["w"]), int(f["h"])))
            # Optional per-frame metadata (e.g., hurtbox/hitbox) passed through to the player
            metas.append({k: v for k, v in f.items() if k not in ("x", "y", "w", "h")})

        self.sheets[state] = {
            "tex": tex,
            "rects": rects,
            "fps": float(fps),
            "durations": frame_durations if frame_durations else None,
            "meta": metas,
        }

    def play(self, state, loop=True, restart=False):
        if self.state != state or restart:
            cfg = self.sheets[state]
            self.state = state
            self._tex = cfg["tex"]
            self._rects = cfg["rects"]
            self._fps = cfg["fps"]
            self._frame_durations = cfg.get("durations")
            self._frame_meta = cfg.get("meta")
            self.frame = 0.0
            self.loop = loop

    def update(self, dt):
        if not self._rects:
            return
        if self._frame_durations:
            # frame is float index; subtract per-frame durations
            idx = int(self.frame)
            if idx >= len(self._frame_durations):
                idx = len(self._frame_durations) - 1
            self.frame += dt / max(1e-6, self._frame_durations[idx])
        else:
            self.frame += self._fps * dt
        n = len(self._rects)
        if self.loop:
            if self.frame >= n:
                self.frame %= n
        else:
            if self.frame >= n:
                self.frame = n - 1e-6

    def finished(self):
        return (not self.loop) and (self.frame >= len(self._rects) - 1)

    def current_texture(self):
        return self._tex

    def current_frame_index(self):
        """Return clamped integer frame index of the current state."""
        if not self._rects:
            return 0
        return max(0, min(int(self.frame), len(self._rects) - 1))

    def current_frame_size(self):
        """Return (w, h) of the current frame in source pixels."""
        if not self._rects:
            return (0, 0)
        idx = self.current_frame_index()
        _, _, w_px, h_px = self._rects[idx]
        return (w_px, h_px)

    def current_frame_rect(self):
        """Return (x, y, w, h) of the current frame in source pixels."""
        if not self._rects:
            return (0, 0, 0, 0)
        idx = self.current_frame_index()
        return self._rects[idx]

    def current_frame_meta(self):
        """Return metadata dict for the current frame (hurtbox/hitbox offsets), if provided."""
        if not self._frame_meta:
            return {}
        idx = self.current_frame_index()
        return self._frame_meta[idx] or {}

    def current_texcoords(self):
        if not self._tex or not self._rects:
            return (0, 0, 1, 0, 1, 1, 0, 1)

        idx = int(self.frame)
        idx = max(0, min(idx, len(self._rects) - 1))
        x_px, y_px, w_px, h_px = self._rects[idx]
        tw, th = self._tex.size

        x0i = x_px / tw
        x1i = (x_px + w_px) / tw
        y0i = y_px / th
        y1i = (y_px + h_px) / th

        # Inset UVs slightly to avoid sampling outside frame bounds (prevents flicker/bleed)
        eps_u = 0.5 / tw
        eps_v = 0.5 / th
        x0i = min(1.0, x0i + eps_u)
        x1i = max(0.0, x1i - eps_u)
        y0i = min(1.0, y0i + eps_v)
        y1i = max(0.0, y1i - eps_v)

        u0 = self._tex.uvpos[0] + x0i * self._tex.uvsize[0]
        u1 = self._tex.uvpos[0] + x1i * self._tex.uvsize[0]
        v0 = self._tex.uvpos[1] + y0i * self._tex.uvsize[1]
        v1 = self._tex.uvpos[1] + y1i * self._tex.uvsize[1]

        if not self.flip_x:
            return (u0, v0, u1, v0, u1, v1, u0, v1)
        else:
            return (u1, v0, u0, v0, u0, v1, u1, v1)
