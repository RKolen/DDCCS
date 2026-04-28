import React from 'react';
import { SkillRow } from '../molecules/SkillRow';
import * as styles from './SkillPanel.module.css';

interface Skill {
  name: string;
  modifier: number;
  proficient: boolean;
}

interface SkillPanelProps {
  skills: Skill[];
}

export function SkillPanel({ skills }: SkillPanelProps): React.ReactElement {
  return (
    <div className={styles.panel}>
      {skills.map((skill, i) => (
        <React.Fragment key={skill.name}>
          <SkillRow
            name={skill.name}
            modifier={skill.modifier}
            proficient={skill.proficient}
          />
          {i < skills.length - 1 && (
            <div className={styles.divider} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
