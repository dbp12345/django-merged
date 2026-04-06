document.addEventListener("DOMContentLoaded", function () {
  // подстрой id под твой селект (у тебя был #suppliestools_select)
  var sel = document.querySelector("#suppliestools_select, select[name='tools__in']");
  if (!sel) return;

  // value -> label из твоего TextChoices
  var labels = {
    supplies: "Supplies needed",
    tools: "Tools needed",
    both: "Supplies and tools needed",
    unknown: "Unknown",
    none: "No supplies or tools needed",
    "": "— empty —"
  };

  Array.prototype.forEach.call(sel.options, function (opt) {
    if (labels.hasOwnProperty(opt.value)) {
      opt.textContent = labels[opt.value];
    }
  });
});
