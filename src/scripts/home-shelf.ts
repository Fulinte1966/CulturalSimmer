for (const shelf of document.querySelectorAll<HTMLElement>(".fm-book-list-frame")) {
  const compactLayout = window.matchMedia(
    "(max-width: 899px), (min-width: 900px) and (max-width: 1199px) and (orientation: portrait)",
  );

  let isDragging = false;
  let didDrag = false;
  let frame = 0;
  let glideFrame = 0;
  let lastMoveTime = 0;
  let lastScrollLeft = 0;
  let pendingScrollLeft = 0;
  let reboundTimer = 0;
  let snapFrame = 0;
  let snapResumeTimer = 0;
  let pressedLink: HTMLAnchorElement | null = null;
  let startX = 0;
  let startScrollLeft = 0;
  let velocity = 0;
  const edgePullLimit = 64;
  const inertialEdgePullLimit = 24;
  const snapDuration = 420;
  const edgeResistance = 0.34;
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const getMaxScroll = () => Math.max(shelf.scrollWidth - shelf.clientWidth, 0);

  const clampScroll = (value: number) => Math.min(Math.max(value, 0), getMaxScroll());

  const getEdgePull = (value: number, limit = edgePullLimit) => {
    const maxScroll = getMaxScroll();
    if (value < 0) return Math.min(-value * edgeResistance, limit);
    if (value > maxScroll) return -Math.min((value - maxScroll) * edgeResistance, limit);
    return 0;
  };

  const setEdgePull = (value: number) => {
    shelf.style.setProperty("--fm-edge-pull", `${value.toFixed(2)}px`);
  };

  const hasEdgePull = () => {
    const currentPull = getComputedStyle(shelf).getPropertyValue("--fm-edge-pull").trim();
    return currentPull && currentPull !== "0px" && currentPull !== "0.00px";
  };

  const clearRebound = () => {
    if (reboundTimer) {
      window.clearTimeout(reboundTimer);
      reboundTimer = 0;
    }
    shelf.classList.remove("is-rebounding");
  };

  const clearSnapAnimation = () => {
    if (snapFrame) {
      cancelAnimationFrame(snapFrame);
      snapFrame = 0;
    }
    shelf.classList.remove("is-snapping");
  };

  const clearSnapResume = () => {
    if (snapResumeTimer) {
      window.clearTimeout(snapResumeTimer);
      snapResumeTimer = 0;
    }
  };

  const pauseSnap = () => {
    clearSnapResume();
    shelf.classList.add("is-snap-paused");
  };

  const resumeSnapAfterRebound = () => {
    clearSnapResume();
    snapResumeTimer = window.setTimeout(() => {
      shelf.classList.remove("is-snap-paused");
      snapResumeTimer = 0;
    }, 160);
  };

  const finishMotion = () => {
    shelf.classList.remove("is-gliding");
    shelf.classList.remove("is-rebounding");
    shelf.classList.remove("is-snapping");
    reboundTimer = 0;
  };

  const reboundEdge = () => {
    clearRebound();
    const currentPull = getComputedStyle(shelf).getPropertyValue("--fm-edge-pull").trim();
    const shouldRebound = currentPull && currentPull !== "0px" && currentPull !== "0.00px";
    if (!shouldRebound) {
      setEdgePull(0);
      shelf.classList.remove("is-snap-paused");
      finishMotion();
      return;
    }
    pauseSnap();
    shelf.classList.add("is-gliding");
    shelf.classList.add("is-rebounding");
    requestAnimationFrame(() => setEdgePull(0));
    reboundTimer = window.setTimeout(() => {
      finishMotion();
      resumeSnapAfterRebound();
    }, 280);
  };

  const getSnapTarget = () => {
    const item = shelf.querySelector<HTMLElement>(".fm-book-list li");
    const itemWidth = item?.getBoundingClientRect().width ?? 180;
    return clampScroll(Math.round(shelf.scrollLeft / itemWidth) * itemWidth);
  };

  const snapToNearest = () => {
    clearSnapAnimation();
    pauseSnap();
    setEdgePull(0);

    const startScrollLeft = shelf.scrollLeft;
    const targetScrollLeft = getSnapTarget();
    const distance = targetScrollLeft - startScrollLeft;

    if (Math.abs(distance) < 1) {
      shelf.scrollLeft = targetScrollLeft;
      finishMotion();
      resumeSnapAfterRebound();
      return;
    }

    shelf.classList.add("is-gliding");
    shelf.classList.add("is-snapping");
    const startTime = performance.now();

    const tick = (time: number) => {
      const progress = Math.min((time - startTime) / snapDuration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      shelf.scrollLeft = startScrollLeft + distance * eased;

      if (progress >= 1) {
        shelf.scrollLeft = targetScrollLeft;
        snapFrame = 0;
        finishMotion();
        resumeSnapAfterRebound();
        return;
      }

      snapFrame = requestAnimationFrame(tick);
    };

    snapFrame = requestAnimationFrame(tick);
  };

  const setScrollWithEdgePull = (value: number, edgeLimit = edgePullLimit) => {
    shelf.scrollLeft = clampScroll(value);
    setEdgePull(getEdgePull(value, edgeLimit));
  };

  const applyScroll = () => {
    setScrollWithEdgePull(pendingScrollLeft);
    frame = 0;
  };

  const stopGlide = () => {
    if (glideFrame) {
      cancelAnimationFrame(glideFrame);
      glideFrame = 0;
    }
    clearSnapAnimation();
    clearRebound();
    shelf.classList.remove("is-gliding");
    shelf.classList.remove("is-snap-paused");
    clearSnapResume();
    setEdgePull(0);
  };

  const settleWithSnap = () => {
    glideFrame = 0;
    if (hasEdgePull()) {
      reboundEdge();
    } else {
      snapToNearest();
    }
  };

  const startGlide = () => {
    if (prefersReducedMotion.matches || Math.abs(velocity) < 0.08) {
      settleWithSnap();
      return;
    }

    shelf.classList.add("is-gliding");
    let previousTime = performance.now();

    const tick = (time: number) => {
      const elapsed = Math.min(time - previousTime, 32);
      previousTime = time;

      const targetScrollLeft = shelf.scrollLeft + velocity * elapsed;
      const hitEdge = targetScrollLeft !== clampScroll(targetScrollLeft);
      const edgeLimit = hitEdge ? inertialEdgePullLimit : edgePullLimit;
      setScrollWithEdgePull(targetScrollLeft, edgeLimit);
      if (hitEdge) {
        settleWithSnap();
        return;
      }
      velocity *= Math.pow(0.92, elapsed / 16.67);

      if (Math.abs(velocity) < 0.02) {
        settleWithSnap();
        return;
      }

      glideFrame = requestAnimationFrame(tick);
    };

    glideFrame = requestAnimationFrame(tick);
  };

  shelf.addEventListener("pointerdown", (event: PointerEvent) => {
    if (compactLayout.matches) return;
    if (event.button !== 0) return;
    stopGlide();
    clearRebound();
    isDragging = true;
    didDrag = false;
    pressedLink = event.target instanceof Element
      ? event.target.closest<HTMLAnchorElement>("a[href]")
      : null;
    velocity = 0;
    startX = event.clientX;
    startScrollLeft = shelf.scrollLeft;
    lastMoveTime = event.timeStamp;
    lastScrollLeft = shelf.scrollLeft;
    shelf.classList.add("is-dragging");
    shelf.setPointerCapture(event.pointerId);
  });

  shelf.addEventListener("pointermove", (event: PointerEvent) => {
    if (compactLayout.matches) return;
    if (!isDragging) return;
    const deltaX = event.clientX - startX;
    if (Math.abs(deltaX) > 3) didDrag = true;
    if (didDrag) event.preventDefault();
    pendingScrollLeft = startScrollLeft - deltaX;
    const elapsed = Math.max(event.timeStamp - lastMoveTime, 1);
    const nextScrollLeft = clampScroll(pendingScrollLeft);
    const nextVelocity = (nextScrollLeft - lastScrollLeft) / elapsed;
    velocity = velocity * 0.65 + nextVelocity * 0.35;
    lastMoveTime = event.timeStamp;
    lastScrollLeft = nextScrollLeft;
    if (!frame) frame = requestAnimationFrame(applyScroll);
  });

  const endDrag = (event: PointerEvent, shouldGlide = false) => {
    if (!isDragging) return;
    isDragging = false;
    shelf.classList.remove("is-dragging");
    if (frame) {
      cancelAnimationFrame(frame);
      applyScroll();
    }
    if (shelf.hasPointerCapture(event.pointerId)) {
      shelf.releasePointerCapture(event.pointerId);
    }
    if (shouldGlide && didDrag) {
      startGlide();
    } else {
      settleWithSnap();
      if (shouldGlide && pressedLink) {
        window.location.href = pressedLink.href;
      }
    }
    pressedLink = null;
  };

  shelf.addEventListener("dragstart", (event) => {
    if (!compactLayout.matches) event.preventDefault();
  });
  shelf.addEventListener("pointerup", (event) => endDrag(event, true));
  shelf.addEventListener("pointercancel", (event) => endDrag(event));
  shelf.addEventListener("pointerleave", (event) => endDrag(event));
  shelf.addEventListener(
    "click",
    (event) => {
      if (!didDrag) return;
      event.preventDefault();
      event.stopPropagation();
      didDrag = false;
    },
    true
  );
}
