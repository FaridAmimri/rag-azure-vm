// The [1], [2] markers in an answer number the chunks retrieved by rag.py, not
// the entries of the sources list, so showing them would point to the wrong link.
// Code is left untouched: `--query [0].name` is not a citation.
const CODE = /(```[\s\S]*?```|`[^`\n]*`)/;
const CITATION = /[ \t]*\[\d+(?:,\s*\d+)*\]/g;

export function stripCitations(answer: string): string {
  return answer
    .split(CODE)
    .map((part, i) => (i % 2 === 1 ? part : part.replace(CITATION, "")))
    .join("");
}
