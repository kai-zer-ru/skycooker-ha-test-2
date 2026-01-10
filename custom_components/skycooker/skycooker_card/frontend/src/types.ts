export interface HomeAssistant {
  language: string;
  states: Record<string, any>;
  // Добавьте другие необходимые свойства из HomeAssistant
}

export interface SkyCookerCardConfig {
  entity_id?: string;
  status_entity?: string;
  temperature_entity?: string;
  remaining_time_entity?: string;
  total_time_entity?: string;
  auto_warm_time_entity?: string;
  success_rate_entity?: string;
  delayed_launch_time_entity?: string;
  current_mode_entity?: string;
  // Добавьте другие параметры конфигурации по мере необходимости
}