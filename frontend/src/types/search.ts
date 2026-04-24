export interface SearchResult {
  id: string;
  nid: number;
  title: string;
  type: string;
  relevance: number;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResult[];
}
