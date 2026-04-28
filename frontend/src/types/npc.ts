export interface NPCRelationship {
  partyMember: string;
  description: string;
}

export interface NPC {
  name:           string;
  role:           string;
  location?:      string;
  alignment?:     string;
  personality:    string;
  backstory?:     string;
  relationships?: Record<string, string>;
  tags?:          string[];
}

export interface NPCQuery {
  nodeNpc: {
    title:            string;
    fieldRole:        string;
    fieldLocation?:   string;
    fieldAlignment?:  string;
    fieldPersonality: string;
    fieldBackstory?:  string;
  } | null;
}

export interface AllNPCsQuery {
  allNodeNpc: {
    nodes: Array<{
      id:               string;
      title:            string;
      fieldRole:        string;
      fieldLocation?:   string;
      fieldAlignment?:  string;
      fieldPersonality: string;
    }>;
  };
}
