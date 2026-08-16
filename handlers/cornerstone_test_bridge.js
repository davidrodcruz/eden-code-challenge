(() => {
  "use strict";

  const BRIDGE_NAME = "__E2E_TEST_BRIDGE__";
  const state = {
    webpackRequire: null,
    tools: null,
    core: null,
    toolsModuleId: null,
    coreModuleId: null,
  };

  const asString = value => (typeof value === "string" ? value : null);

  const asNumber = value =>
    typeof value === "number" && Number.isFinite(value) ? value : null;

  const asVector = value => {
    if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
      return null;
    }

    const vector = Array.from(value, asNumber);
    return vector.length === 3 && vector.every(value => value !== null)
      ? vector
      : null;
  };

  const asPoint2D = value => {
    if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
      return null;
    }

    const point = Array.from(value, asNumber);
    return point.length === 2 && point.every(value => value !== null)
      ? point
      : null;
  };

  const call = (object, method, ...args) => {
    try {
      return object && typeof object[method] === "function"
        ? object[method](...args)
        : null;
    } catch (_error) {
      return null;
    }
  };

  const toSerializable = value => JSON.parse(JSON.stringify(value));

  function findTools(require) {
    if (state.tools) {
      return state.tools;
    }

    const modules = require && require.m;
    if (!modules) {
      return null;
    }

    for (const moduleId of Object.keys(modules)) {
      const source = String(modules[moduleId]);
      if (
        !source.includes("ToolGroupManager") ||
        !source.includes("annotation:")
      ) {
        continue;
      }

      try {
        const candidate = require(moduleId);
        if (
          candidate?.annotation?.state?.getAllAnnotations &&
          candidate?.annotation?.state?.getAnnotationManager &&
          candidate?.ToolGroupManager?.getAllToolGroups
        ) {
          state.tools = candidate;
          state.toolsModuleId = moduleId;
          return candidate;
        }
      } catch (_error) {
        // A matching module can be a lazy chunk that is not initialized yet.
      }
    }

    return null;
  }

  function findCore(require) {
    if (state.core) {
      return state.core;
    }

    const modules = require && require.m;
    if (!modules) {
      return null;
    }

    for (const moduleId of Object.keys(modules)) {
      const source = String(modules[moduleId]);
      if (
        !source.includes("lD:") ||
        !source.includes("qO:") ||
        !source.includes("getAll")
      ) {
        continue;
      }

      try {
        const candidate = require(moduleId);
        if (typeof candidate?.lD === "function") {
          state.core = candidate;
          state.coreModuleId = moduleId;
          return candidate;
        }
      } catch (_error) {
        // Core is optional for annotation extraction.
      }
    }

    return null;
  }

  function capture(require) {
    if (typeof require !== "function") {
      return;
    }

    state.webpackRequire = require;
    findTools(require);
    findCore(require);
  }

  function wrapChunk(chunk) {
    if (!Array.isArray(chunk) || typeof chunk[2] !== "function") {
      return;
    }

    if (chunk[2].__e2eBridgeWrapped) {
      return;
    }

    const runtime = chunk[2];
    const wrappedRuntime = function (...args) {
      capture(args[0]);
      return runtime.apply(this, args);
    };
    Object.defineProperty(wrappedRuntime, "__e2eBridgeWrapped", {
      value: true,
    });
    chunk[2] = wrappedRuntime;
  }

  function captureFromExistingChunk() {
    if (state.webpackRequire || !window.webpackChunk?.push) {
      return;
    }

    try {
      window.webpackChunk.push(
        [[`e2e_test_bridge_${Date.now()}`], {}, require => capture(require)]
      );
    } catch (_error) {
      // Webpack has not installed its runtime callback yet.
    }
  }

  const originalChunk = Array.isArray(window.webpackChunk)
    ? window.webpackChunk
    : [];

  const chunkProxy = new Proxy(originalChunk, {
    set(target, property, value, receiver) {
      if (
        property === "push" &&
        typeof value === "function" &&
        !value.__e2eBridgeWrapped
      ) {
        const originalPush = value;
        value = function (...chunks) {
          chunks.forEach(wrapChunk);
          return originalPush.apply(this, chunks);
        };
        Object.defineProperty(value, "__e2eBridgeWrapped", { value: true });
      }

      return Reflect.set(target, property, value, receiver);
    },
  });

  try {
    Object.defineProperty(window, "webpackChunk", {
      configurable: true,
      get: () => chunkProxy,
      set: value => {
        if (Array.isArray(value)) {
          value.forEach(wrapChunk);
        }
      },
    });
  } catch (_error) {
    if (Array.isArray(originalChunk) && typeof originalChunk.push === "function") {
      const originalPush = originalChunk.push;
      originalChunk.push = function (...chunks) {
        chunks.forEach(wrapChunk);
        return originalPush.apply(this, chunks);
      };
    }
  }

  originalChunk.forEach(wrapChunk);

  function getTools() {
    captureFromExistingChunk();
    return findTools(state.webpackRequire);
  }

  function getCore() {
    captureFromExistingChunk();
    return findCore(state.webpackRequire);
  }

  function getManager() {
    const tools = getTools();
    return tools?.annotation?.state?.getAnnotationManager?.() || null;
  }

  function getViewportState(viewportId) {
    const core = getCore();
    const id = String(viewportId);
    const engine = core ? call(core, "lD", "renderingEngine") : null;
    const viewport = call(engine, "getViewport", id);
    if (!viewport) {
      return null;
    }

    const camera = call(viewport, "getCamera");
    return toSerializable({
      viewportId: id,
      currentImageIdIndex: asNumber(call(viewport, "getCurrentImageIdIndex")),
      sliceIndex: asNumber(call(viewport, "getSliceIndex")),
      currentImageId: asString(call(viewport, "getCurrentImageId")),
      frameOfReferenceUID: asString(
        call(viewport, "getFrameOfReferenceUID")
      ),
      volumeId: asString(call(viewport, "getVolumeId")),
      camera: camera
        ? {
            viewPlaneNormal: asVector(camera.viewPlaneNormal),
            viewUp: asVector(camera.viewUp),
            focalPoint: asVector(camera.focalPoint),
            position: asVector(camera.position),
            parallelProjection: camera.parallelProjection === true,
            parallelScale: asNumber(camera.parallelScale),
          }
        : null,
    });
  }

  function getViewportIds(tools) {
    const ids = new Set();
    for (const group of call(tools?.ToolGroupManager, "getAllToolGroups") || []) {
      for (const info of group.viewportsInfo || []) {
        if (info.viewportId !== undefined && info.viewportId !== null) {
          ids.add(String(info.viewportId));
        }
      }
    }
    return [...ids];
  }

  function annotationBelongsToViewport(annotation, viewportId) {
    if (viewportId === undefined || viewportId === null) {
      return true;
    }

    const viewport = getViewportState(viewportId);
    if (!viewport) {
      return true;
    }

    const metadata = annotation?.metadata || {};
    if (
      metadata.FrameOfReferenceUID &&
      viewport.frameOfReferenceUID &&
      metadata.FrameOfReferenceUID !== viewport.frameOfReferenceUID
    ) {
      return false;
    }

    const annotationNormal = asVector(metadata.viewPlaneNormal);
    const viewportNormal = asVector(viewport.camera?.viewPlaneNormal);
    if (!annotationNormal || !viewportNormal) {
      return true;
    }

    const dot = annotationNormal.reduce(
      (sum, value, index) => sum + value * viewportNormal[index],
      0
    );
    return Math.abs(dot) >= 0.999;
  }

  function annotationIsOnCurrentSlice(annotation, viewportId) {
    const viewport = getViewportState(viewportId);
    if (!viewport) {
      return true;
    }

    const metadata = annotation?.metadata || {};
    if (metadata.referencedImageId && viewport.currentImageId) {
      return metadata.referencedImageId === viewport.currentImageId;
    }

    if (metadata.sliceIndex !== undefined && viewport.sliceIndex !== null) {
      return Number(metadata.sliceIndex) === viewport.sliceIndex;
    }

    return annotationBelongsToViewport(annotation, viewportId);
  }

  function normalizeStats(cachedStats) {
    const measurements = [];
    if (!cachedStats || typeof cachedStats !== "object") {
      return measurements;
    }

    const metricNames = [
      "length",
      "area",
      "angle",
      "value",
      "perimeter",
      "radius",
      "mean",
      "stdDev",
      "max",
    ];

    for (const [statsKey, stats] of Object.entries(cachedStats)) {
      if (!stats || typeof stats !== "object") {
        continue;
      }

      const values = {};
      for (const metricName of metricNames) {
        const value = asNumber(stats[metricName]);
        if (value !== null) {
          values[metricName] = value;
        }
      }

      const unit =
        asString(stats.unit) ||
        asString(stats.areaUnit) ||
        asString(stats.radiusUnit) ||
        asString(stats.modalityUnit);

      if (Object.keys(values).length || unit !== null) {
        measurements.push({ statsKey, values, unit });
      }
    }

    return measurements;
  }

  function primaryMeasurement(measurements) {
    const primaryMetricNames = [
      "length",
      "area",
      "angle",
      "value",
      "perimeter",
      "radius",
    ];

    for (const measurement of measurements) {
      const metric = primaryMetricNames.find(
        metricName => measurement.values[metricName] !== undefined
      );
      if (metric) {
        return {
          value: measurement.values[metric],
          metric,
          unit: measurement.unit,
          statsKey: measurement.statsKey,
        };
      }
    }

    return { value: null, metric: null, unit: null, statsKey: null };
  }

  function normalizeAnnotation(annotation) {
    const metadata = annotation?.metadata || {};
    const data = annotation?.data || {};
    const points = Array.isArray(data.handles?.points)
      ? data.handles.points.map(asVector).filter(Boolean)
      : [];
    const measurements = normalizeStats(data.cachedStats);

    return {
      uid: asString(annotation?.annotationUID),
      toolName: asString(metadata.toolName),
      frameOfReferenceUID: asString(metadata.FrameOfReferenceUID),
      referencedImageId: asString(metadata.referencedImageId),
      volumeId: asString(metadata.volumeId),
      sliceIndex: asNumber(metadata.sliceIndex),
      viewPlaneNormal: asVector(metadata.viewPlaneNormal),
      viewUp: asVector(metadata.viewUp),
      cameraFocalPoint: asVector(metadata.cameraFocalPoint),
      cameraPosition: asVector(metadata.cameraPosition),
      points,
      measurement: primaryMeasurement(measurements),
      measurements,
      state: {
        highlighted: annotation?.highlighted === true,
        invalidated: annotation?.invalidated === true,
        isLocked: annotation?.isLocked === true,
        isVisible: annotation?.isVisible !== false,
      },
    };
  }

  function getAnnotations(options = {}) {
    if (typeof options !== "object" || options === null) {
      options = { viewportId: options };
    }

    const manager = getManager();
    if (!manager) {
      throw new Error("Cornerstone annotation manager is not ready");
    }

    const annotations = manager
      .getAllAnnotations()
      .filter(annotation =>
        options.toolName
          ? annotation?.metadata?.toolName === options.toolName
          : true
      )
      .filter(annotation =>
        annotationBelongsToViewport(annotation, options.viewportId)
      )
      .filter(annotation =>
        options.visibility === "current-slice"
          ? annotationIsOnCurrentSlice(annotation, options.viewportId)
          : true
      )
      .map(annotation => ({
        ...normalizeAnnotation(annotation),
        visibleOnViewport:
          options.viewportId === undefined || options.viewportId === null
            ? null
            : annotationIsOnCurrentSlice(annotation, options.viewportId),
      }));

    return toSerializable({
      schemaVersion: 1,
      source: "cornerstoneTools.annotation.state",
      count: annotations.length,
      annotations,
    });
  }

  function getVisibleAnnotations(options = {}) {
    if (typeof options !== "object" || options === null) {
      options = { viewportId: options };
    }
    return getAnnotations({ ...options, visibility: "current-slice" });
  }

  function getAnnotationByUid(argument) {
    const options =
      argument && typeof argument === "object" ? argument : {};
    const annotationUID =
      argument && typeof argument === "object" ? argument.uid : argument;
    const manager = getManager();
    if (!manager) {
      throw new Error("Cornerstone annotation manager is not ready");
    }

    const annotation = manager
      .getAllAnnotations()
      .find(candidate => candidate?.annotationUID === annotationUID);
    if (!annotation) {
      return null;
    }

    return toSerializable({
      ...normalizeAnnotation(annotation),
      visibleOnViewport:
        options?.viewportId === undefined || options?.viewportId === null
          ? null
          : annotationIsOnCurrentSlice(annotation, options.viewportId),
    });
  }

  function worldToCanvas(argument) {
    const viewportId = argument?.viewportId;
    const worldPoint = argument?.worldPoint;
    const core = getCore();
    const point = asVector(worldPoint);
    const id = String(viewportId);
    const engine = core ? call(core, "lD", "renderingEngine") : null;
    const viewport = call(engine, "getViewport", id);
    const canvasPoint = viewport && point
      ? asPoint2D(call(viewport, "worldToCanvas", point))
      : null;

    return toSerializable({
      viewportId: id,
      worldPoint: point,
      canvasPoint,
    });
  }

  function getActiveTools() {
    const tools = getTools();
    if (!tools) {
      return toSerializable({ schemaVersion: 1, groups: [] });
    }

    const groups = (call(tools.ToolGroupManager, "getAllToolGroups") || []).map(
      group => ({
        id: asString(group.id),
        currentActiveTool: asString(group.currentActivePrimaryToolName),
        activeTools: Object.entries(group.toolOptions || {})
          .filter(([, option]) => option?.mode === "Active")
          .map(([toolName]) => asString(toolName))
          .filter(Boolean),
      })
    );

    return toSerializable({ schemaVersion: 1, groups });
  }

  function getState(options = {}) {
    if (!options || typeof options !== "object") {
      options = {};
    }

    const tools = getTools();
    const requestedIds = Array.isArray(options.viewportIds)
      ? options.viewportIds.map(String)
      : getViewportIds(tools);

    return toSerializable({
      schemaVersion: 1,
      source: "cornerstoneTools.annotation.state",
      annotations: getAnnotations(options).annotations,
      viewports: requestedIds
        .map(getViewportState)
        .filter(Boolean),
      activeTools: getActiveTools().groups,
    });
  }

  const bridge = {
    schemaVersion: 1,
    status: () => {
      captureFromExistingChunk();
      return toSerializable({
        schemaVersion: 1,
        ready: Boolean(getTools()),
        toolsAvailable: Boolean(state.tools),
        coreAvailable: Boolean(getCore()),
        source: state.tools
          ? "cornerstoneTools.annotation.state"
          : null,
      });
    },
    getAnnotations,
    getAnnotationCount: options => getAnnotations(options).count,
    getVisibleAnnotations,
    getVisibleAnnotationCount: options => getVisibleAnnotations(options).count,
    getAnnotationByUid,
    worldToCanvas,
    getViewportState,
    getActiveTools,
    getState,
    clearAnnotations: options => {
      const manager = getManager();
      if (!manager) {
        throw new Error("Cornerstone annotation manager is not ready");
      }

      if (options === null || typeof options !== "object") {
        options = {};
      }
      const tools = getTools();
      const annotations = manager
        .getAllAnnotations()
        .filter(annotation =>
          annotationBelongsToViewport(annotation, options.viewportId)
        );
      annotations.forEach(annotation =>
        tools.annotation.state.removeAnnotation(annotation.annotationUID)
      );
      return toSerializable({
        schemaVersion: 1,
        removedCount: annotations.length,
      });
    },
  };

  Object.defineProperty(bridge, "__e2eBridge", { value: true });
  window[BRIDGE_NAME] = bridge;
})();
