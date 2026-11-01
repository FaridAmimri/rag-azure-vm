// Shapes of the RAG API (same fields as the Pydantic models in api.py)

export type Source = {
  title: string;
  source: string; // path of the .md file in the corpus
  url: string; // link to the page on learn.microsoft.com
};

export type AskResponse = {
  answer: string;
  sources: Source[];
};

// Body returned by /api/ask when something goes wrong
export type ErrorResponse = {
  error: string;
};
