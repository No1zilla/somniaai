(function () {
  const listEl = document.getElementById("articles-list");
  const searchEl = document.getElementById("blog-search");
  const yearEl = document.getElementById("blog-year");
  const totalEl = document.getElementById("articles-total");
  const pagesEl = document.getElementById("pagination");

  if (!listEl || !searchEl || !yearEl || !totalEl || !pagesEl) {
    return;
  }

  const monthNames = [
    "янв",
    "фев",
    "мар",
    "апр",
    "мая",
    "июн",
    "июл",
    "авг",
    "сен",
    "окт",
    "ноя",
    "дек",
  ];

  const rawItems = Array.from(listEl.querySelectorAll("li a")).map((anchor) => {
    const href = anchor.getAttribute("href") || "";
    const title = (anchor.textContent || "").trim();
    const match = href.match(/^(\d{4})-(\d{2})-(\d{2})-/);

    let year = "без даты";
    let dateLabel = "Без даты";

    if (match) {
      year = match[1];
      const monthIndex = Number(match[2]) - 1;
      const day = Number(match[3]);
      dateLabel = `${day} ${monthNames[monthIndex] || ""} ${year}`.trim();
    }

    return {
      href,
      title,
      titleLc: title.toLowerCase(),
      year,
      dateLabel,
      excerpt: `${title.slice(0, 120)}${title.length > 120 ? "..." : ""}`,
    };
  });

  const years = Array.from(
    new Set(rawItems.map((item) => item.year).filter((year) => /^\d{4}$/.test(year)))
  ).sort((a, b) => Number(b) - Number(a));

  for (const year of years) {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearEl.appendChild(option);
  }

  const pageSize = 24;
  let currentPage = 1;
  let filtered = rawItems;

  const getFilteredItems = () => {
    const query = searchEl.value.trim().toLowerCase();
    const year = yearEl.value;

    return rawItems.filter((item) => {
      const matchesQuery = !query || item.titleLc.includes(query);
      const matchesYear = year === "all" || item.year === year;
      return matchesQuery && matchesYear;
    });
  };

  const renderPage = () => {
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
    if (currentPage > totalPages) {
      currentPage = totalPages;
    }

    const start = (currentPage - 1) * pageSize;
    const visible = filtered.slice(start, start + pageSize);

    listEl.innerHTML = "";

    if (!visible.length) {
      const empty = document.createElement("li");
      empty.className = "empty-state";
      empty.textContent = "По вашему запросу статьи не найдены.";
      listEl.appendChild(empty);
      totalEl.textContent = "0 статей";
      pagesEl.innerHTML = "";
      return;
    }

    const articleWord = filtered.length % 10 === 1 && filtered.length % 100 !== 11 ? "статья" : "статей";
    totalEl.textContent = `${filtered.length} ${articleWord}`;

    for (const item of visible) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = item.href;

      const date = document.createElement("div");
      date.className = "article-date";
      date.textContent = item.dateLabel;

      const title = document.createElement("h2");
      title.className = "article-title";
      title.textContent = item.title;

      const excerpt = document.createElement("p");
      excerpt.className = "article-excerpt";
      excerpt.textContent = item.excerpt;

      a.appendChild(date);
      a.appendChild(title);
      a.appendChild(excerpt);
      li.appendChild(a);
      listEl.appendChild(li);
    }

    pagesEl.innerHTML = "";
    if (totalPages === 1) {
      return;
    }

    for (let page = 1; page <= totalPages; page += 1) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = String(page);
      if (page === currentPage) {
        btn.setAttribute("aria-current", "page");
      }
      btn.addEventListener("click", () => {
        currentPage = page;
        renderPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      pagesEl.appendChild(btn);
    }
  };

  const applyFilters = () => {
    filtered = getFilteredItems();
    currentPage = 1;
    renderPage();
  };

  searchEl.addEventListener("input", applyFilters);
  yearEl.addEventListener("change", applyFilters);

  applyFilters();
})();
