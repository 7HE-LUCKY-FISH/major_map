const CATALOG_SEARCH_BASE = "https://catalog.sjsu.edu/search_advanced.php";
const CATALOG_DEFAULT_PARAMS = {
  cur_cat_oid: "10",
  search_database: "Search",
  search_db: "Search",
  cpage: "1",
  ecpage: "1",
  ppage: "1",
  spage: "1",
  tpage: "1",
  location: "33",
  "filter[exact_match]": "1"
};

const normalizeCourseCode = (courseCode) => {
  if (!courseCode) return "";
  const cleaned = String(courseCode).trim();
  if (!cleaned) return "";

  // Insert a space between dept letters and course number when missing (e.g., CS46A -> CS 46A)
  const spaced = cleaned.replace(/^([A-Za-z]+)(\d)/, "$1 $2");

  return spaced.replace(/\s+/g, " ");
};

export const getCourseLink = (courseCode) => {
  const normalized = normalizeCourseCode(courseCode);
  if (!normalized) return "";
  const params = new URLSearchParams({
    ...CATALOG_DEFAULT_PARAMS,
    "filter[keyword]": normalized
  });
  return `${CATALOG_SEARCH_BASE}?${params.toString()}`;
};
