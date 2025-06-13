export interface AnalysisData {
  basic_stats: {
    total_conversations: number;
    total_messages: number;
    role_stats: {
      user: number;
      assistant: number;
    };
    avg_conversation_length: number;
  };
  patterns: {
    user_first: number;
    assistant_first: number;
    avg_turn_length: number;
    max_turn_length: number;
  };
  keywords: {
    [key: string]: number;
  };
} 