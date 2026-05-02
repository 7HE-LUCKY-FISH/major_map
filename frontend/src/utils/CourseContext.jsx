import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getPlannerState, updatePlannerState } from "../api/api";
import { AuthContext } from "./AuthContext";
import { CourseContext } from "./CourseContext";

const GUEST_STORAGE_KEY = "guestPlannerState";

const DEFAULT_MAJOR_STATE = {
  completedCourses: [],
  selectedMajor: "",
  submitted: false,
  preferredUnits: 15,
};

const DEFAULT_SCHEDULE_STATE = {
  courseCodes: [],
  schedules: [],
  professorFreqs: {},
  selectedScheduleIndex: 0,
};

const DEFAULT_PLANNER_STATE = {
  major: DEFAULT_MAJOR_STATE,
  roadmap: [],
  schedule: DEFAULT_SCHEDULE_STATE,
};

const normalizePlannerState = (plannerState = {}) => ({
  major: {
    ...DEFAULT_MAJOR_STATE,
    ...(plannerState.major || {}),
  },
  roadmap: Array.isArray(plannerState.roadmap) ? plannerState.roadmap : [],
  schedule: {
    ...DEFAULT_SCHEDULE_STATE,
    ...(plannerState.schedule || {}),
  },
});

const readGuestPlannerState = () => {
  try {
    const raw = localStorage.getItem(GUEST_STORAGE_KEY);
    if (!raw) {
      return DEFAULT_PLANNER_STATE;
    }
    return normalizePlannerState(JSON.parse(raw));
  } catch {
    return DEFAULT_PLANNER_STATE;
  }
};

const isEqual = (left, right) => JSON.stringify(left) === JSON.stringify(right);

export const CourseProvider = ({ children }) => {
  const { user, authLoading } = useContext(AuthContext);
  const [plannerState, setPlannerState] = useState(DEFAULT_PLANNER_STATE);
  const [storageReady, setStorageReady] = useState(false);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    let isMounted = true;

    const loadPlannerState = async () => {
      setStorageReady(false);

      if (!user) {
        if (isMounted) {
          setPlannerState(readGuestPlannerState());
          setStorageReady(true);
        }
        return;
      }

      try {
        const savedPlannerState = await getPlannerState();
        if (isMounted) {
          setPlannerState(normalizePlannerState(savedPlannerState));
        }
      } catch {
        if (isMounted) {
          setPlannerState(DEFAULT_PLANNER_STATE);
        }
      } finally {
        if (isMounted) {
          setStorageReady(true);
        }
      }
    };

    loadPlannerState();

    return () => {
      isMounted = false;
    };
  }, [user, authLoading]);

  useEffect(() => {
    if (!storageReady) {
      return;
    }

    if (!user) {
      localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(plannerState));
      return;
    }

    const timeoutId = window.setTimeout(() => {
      updatePlannerState(plannerState).catch((error) => {
        console.error("Failed to save planner state:", error);
      });
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [plannerState, storageReady, user]);

  const setCompletedCourses = useCallback((value) => {
    setPlannerState((prev) => {
      const nextValue =
        typeof value === "function" ? value(prev.major.completedCourses) : value;
      if (isEqual(prev.major.completedCourses, nextValue)) {
        return prev;
      }
      return {
        ...prev,
        major: {
          ...prev.major,
          completedCourses: nextValue,
        },
      };
    });
  }, []);

  const setSelectedMajor = useCallback((value) => {
    setPlannerState((prev) => {
      const nextValue =
        typeof value === "function" ? value(prev.major.selectedMajor) : value;
      if (prev.major.selectedMajor === nextValue) {
        return prev;
      }
      return {
        ...prev,
        major: {
          ...prev.major,
          selectedMajor: nextValue,
        },
      };
    });
  }, []);

  const setSubmitted = useCallback((value) => {
    setPlannerState((prev) => {
      const nextValue =
        typeof value === "function" ? value(prev.major.submitted) : value;
      if (prev.major.submitted === nextValue) {
        return prev;
      }
      return {
        ...prev,
        major: {
          ...prev.major,
          submitted: nextValue,
        },
      };
    });
  }, []);

  const setRoadmap = useCallback((value) => {
    setPlannerState((prev) => {
      const nextValue =
        typeof value === "function" ? value(prev.roadmap) : value;
      const normalizedValue = Array.isArray(nextValue) ? nextValue : [];
      if (isEqual(prev.roadmap, normalizedValue)) {
        return prev;
      }
      return {
        ...prev,
        roadmap: normalizedValue,
      };
    });
  }, []);

  const setScheduleState = useCallback((value) => {
    setPlannerState((prev) => {
      const nextValue =
        typeof value === "function" ? value(prev.schedule) : value;
      const normalizedValue = {
        ...DEFAULT_SCHEDULE_STATE,
        ...nextValue,
      };
      if (isEqual(prev.schedule, normalizedValue)) {
        return prev;
      }
      return {
        ...prev,
        schedule: normalizedValue,
      };
    });
  }, []);

  const setPreferredUnits = useCallback((value) => {
    setPlannerState((prev) => {
      const nextValue = typeof value === "function" ? value(prev.major.preferredUnits) : value;
      if (prev.major.preferredUnits === nextValue) return prev;
      return {
        ...prev,
        major: {
          ...prev.major,
          preferredUnits: nextValue,
        },
      };
    });
  }, []);

  const contextValue = useMemo(() => ({
    completedCourses: plannerState.major.completedCourses,
    setCompletedCourses,
    selectedMajor: plannerState.major.selectedMajor,
    setSelectedMajor,
    submitted: plannerState.major.submitted,
    setSubmitted,
    roadmap: plannerState.roadmap,
    setRoadmap,
    scheduleState: plannerState.schedule,
    setScheduleState,
    plannerLoading: authLoading || !storageReady,
    setPreferredUnits,
    preferredUnits: plannerState.major.preferredUnits,
  }), [
    authLoading,
    plannerState.major.completedCourses,
    plannerState.major.selectedMajor,
    plannerState.major.submitted,
    plannerState.roadmap,
    plannerState.schedule,
    plannerState.major.preferredUnits,
    setCompletedCourses,
    setRoadmap,
    setScheduleState,
    setSelectedMajor,
    setSubmitted,
    setPreferredUnits,
    storageReady,
  ]);

  return (
    <CourseContext.Provider value={contextValue}>
      {children}
    </CourseContext.Provider>
  );
};
