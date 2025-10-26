"""
AI Integration Component for Character Consultant

Provides AI-powered consultation features with graceful fallback to rule-based methods.
"""

from typing import Dict, Any

from src.ai.availability import AI_AVAILABLE, CharacterAIConfig


class AIConsultant:
    """Handles AI-powered character consultations."""

    def __init__(self, profile, class_knowledge, ai_client=None):
        """
        Initialize AI consultant.

        Args:
            profile: CharacterProfile instance
            class_knowledge: Class knowledge dictionary
            ai_client: Optional global AI client
        """
        self.profile = profile
        self.class_knowledge = class_knowledge
        self.ai_client = ai_client
        self._character_ai_client = None

    def get_ai_client(self):
        """
        Get the appropriate AI client for this character.

        Returns:
            Character-specific client if configured, otherwise global client, or None
        """
        if not AI_AVAILABLE:
            return None

        # Create character-specific client if configured and not yet created
        if self.profile.ai_config and not self._character_ai_client:
            if isinstance(self.profile.ai_config, CharacterAIConfig):
                self._character_ai_client = self.profile.ai_config.create_client(
                    self.ai_client
                )
            elif isinstance(
                self.profile.ai_config, dict
            ) and self.profile.ai_config.get("enabled"):
                # Convert dict to CharacterAIConfig
                config = CharacterAIConfig.from_dict(self.profile.ai_config)
                self._character_ai_client = config.create_client(self.ai_client)

        # Return character-specific or global client
        return self._character_ai_client or self.ai_client

    def build_character_system_prompt(self) -> str:
        """
        Build a system prompt that describes this character for AI roleplay.

        Returns:
            System prompt string for AI
        """
        prompt_parts = [
            f"You are {self.profile.name}, a {self.profile.character_class.value}"
            " in a D&D 5e campaign.",
            f"You are level {self.profile.level}.",
        ]

        if self.profile.background_story:
            prompt_parts.append(
                f"\nYour background: {self.profile.background_story[:500]}"
            )

        if self.profile.personality_summary:
            prompt_parts.append(
                f"\nYour personality: {self.profile.personality_summary}"
            )

        if self.profile.motivations:
            prompt_parts.append(
                f"\nYour motivations: {', '.join(self.profile.motivations)}"
            )

        if self.profile.goals:
            prompt_parts.append(f"\nYour goals: {', '.join(self.profile.goals)}")

        if self.profile.fears_weaknesses:
            prompt_parts.append(
                f"\nYour fears/weaknesses: {', '.join(self.profile.fears_weaknesses)}"
            )

        # Add class knowledge
        if self.class_knowledge:
            decision_style = self.class_knowledge.get(
                "decision_style", "act according to your class"
            )
            prompt_parts.append(
                f"\nAs a {self.profile.character_class.value}, "
                f"you typically: {decision_style}"
            )

        prompt_parts.append(
            "\nWhen responding, stay in character and consider your personality, "
            "motivations, and class nature."
        )

        return "\n".join(prompt_parts)

    def suggest_reaction_ai(
        self,
        situation: str,
        context: Dict[str, Any] = None,
        base_suggestion: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        AI-enhanced character reaction suggestion.

        Args:
            situation: Description of the situation
            context: Optional context information
            base_suggestion: Rule-based suggestion to enhance (required)

        Returns:
            Dictionary with AI-enhanced reaction suggestions
        """
        if base_suggestion is None:
            raise ValueError("base_suggestion is required for AI enhancement")

        # Try AI enhancement
        ai_client = self.get_ai_client()
        if not ai_client:
            base_suggestion["ai_enhanced"] = False
            return base_suggestion

        try:
            # Build prompt for AI
            system_prompt = self.build_character_system_prompt()

            # Custom system prompt from character config
            if self.profile.ai_config and isinstance(self.profile.ai_config, dict):
                custom_prompt = self.profile.ai_config.get("system_prompt")
                if custom_prompt:
                    system_prompt = custom_prompt
            elif self.profile.ai_config and hasattr(
                self.profile.ai_config, "system_prompt"
            ):
                if self.profile.ai_config.system_prompt:
                    system_prompt = self.profile.ai_config.system_prompt

            # Create context string
            context_str = ""
            if context:
                context_str = "\n\nAdditional context:\n" + "\n".join(
                    [f"- {k}: {v}" for k, v in context.items()]
                )

            user_prompt = f"""Given this situation: {situation}{context_str}

How would you react? Consider:
1. Your immediate emotional/instinctive response
2. What you would say or do
3. How this aligns with your goals and personality
4. Any class abilities or knowledge you might use

Provide a natural, in-character response."""

            messages = [
                ai_client.create_system_message(system_prompt),
                ai_client.create_user_message(user_prompt),
            ]

            ai_response = ai_client.chat_completion(messages)

            # Add AI response to base suggestion
            base_suggestion["ai_response"] = ai_response
            base_suggestion["ai_enhanced"] = True

        except (
            ImportError,
            AttributeError,
            KeyError,
            ValueError,
            ConnectionError,
            TimeoutError,
        ) as e:
            # AI failed, fall back to rule-based
            base_suggestion["ai_error"] = str(e)
            base_suggestion["ai_enhanced"] = False

        return base_suggestion

    def suggest_dc_for_action_ai(
        self,
        action: str,
        _context: Dict[str, Any] = None,
        base_suggestion: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        AI-enhanced DC suggestion.

        Args:
            action: Action description
            context: Optional context information
            base_suggestion: Rule-based DC suggestion to enhance (required)

        Returns:
            Dictionary with AI-enhanced DC suggestion
        """
        if base_suggestion is None:
            raise ValueError("base_suggestion is required for AI enhancement")

        ai_client = self.get_ai_client()
        if not ai_client:
            base_suggestion["ai_enhanced"] = False
            return base_suggestion

        try:
            # Build a prompt for DC suggestion
            key_features = ", ".join(self.class_knowledge.get("key_features", []))
            system_prompt = (
                f"You are a D&D 5e Dungeon Master helping determine"
                f" appropriate DCs for character actions.\n\n"
                f"Character: {self.profile.name} "
                f"({self.profile.character_class.value} Level {self.profile.level})\n"
                f"Class abilities: {key_features}"
            )

            if self.profile.background_story:
                system_prompt += f"\nBackground: {self.profile.background_story[:300]}"

            user_prompt = f"""The character wants to: {action}

Consider:
1. Standard DC guidelines (5=very easy, 10=easy, 15=medium, 20=hard, 25=very hard, 30=nearly impossible)
2. Character's class abilities and level
3. Situational modifiers

Suggest an appropriate DC (5-30) and explain why. Also suggest if the character has
any advantages for this action."""

            messages = [
                ai_client.create_system_message(system_prompt),
                ai_client.create_user_message(user_prompt),
            ]

            ai_response = ai_client.chat_completion(messages)

            base_suggestion["ai_analysis"] = ai_response
            base_suggestion["ai_enhanced"] = True

        except (
            ImportError,
            AttributeError,
            KeyError,
            ValueError,
            ConnectionError,
            TimeoutError,
        ) as e:
            base_suggestion["ai_error"] = str(e)
            base_suggestion["ai_enhanced"] = False

        return base_suggestion
