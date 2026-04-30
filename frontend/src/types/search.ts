export interface SearchResult {
  id: string;
  nid: number;
  title: string;
  type: string;
  relevance: number;
  match_type: 'exact' | 'keyword' | 'semantic';
}

export interface SearchFilters {
  equipment: string[];
  species: string[];
  class: string[];
  campaign: string[];
}

export interface SearchDecomposition {
  backends: string[];
  entity_types: string[];
  filters: SearchFilters;
  semantic_query: string;
  keyword_query: string;
}

export interface SearchResponse {
  query: string;
  count: number;
  decomposition?: SearchDecomposition;
  results: SearchResult[];
}
