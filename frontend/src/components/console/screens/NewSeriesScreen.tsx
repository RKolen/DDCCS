/**
 * NewSeriesScreen — `stories/new-series`.
 *
 * AI-powered wizard to draft a new story series outline.
 * Dispatches to the Python AI worker via the activity drawer.
 *
 * Port of `NewSeriesWizardScreen` from screens-router.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { AiTag, Icon } from '../atoms';

const GENRES = ['Dark fantasy', 'Heroic', 'Mystery', 'Horror'];
const LENGTHS = ['3-5 stories', '6-10 stories', '11+ stories'];

export function NewSeriesScreen({ ctx }: ScreenProps): React.ReactElement {
  const [genre, setGenre]   = React.useState(GENRES[0]);
  const [length, setLength] = React.useState(LENGTHS[1]);

  void ctx;

  return (
    <div className="screen-newseries">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">New series <AiTag label="AI" /></span>
          <h2>Start a story series</h2>
          <p className="screen-blurb">
            Drafts an outline, opening hook, and inciting incident from a one-line premise.
          </p>
        </div>
      </header>

      <div className="wizard">
        <ol className="wizard-steps">
          <li className="active"><span>1</span> Premise</li>
          <li><span>2</span> Tone &amp; constraints</li>
          <li><span>3</span> Party</li>
          <li><span>4</span> Review</li>
        </ol>

        <div className="wizard-pane">
          <label className="form-row">
            <span>One-line premise</span>
            <input type="text" placeholder='e.g. "A bell rings in a village that has no bell."' />
          </label>

          <label className="form-row">
            <span>Genre</span>
            <div className="seg-control">
              {GENRES.map(g => (
                <button
                  key={g}
                  type="button"
                  className={`seg${g === genre ? ' active' : ''}`}
                  onClick={() => setGenre(g)}
                >
                  {g}
                </button>
              ))}
            </div>
          </label>

          <label className="form-row">
            <span>Series length</span>
            <div className="seg-control">
              {LENGTHS.map(l => (
                <button
                  key={l}
                  type="button"
                  className={`seg${l === length ? ' active' : ''}`}
                  onClick={() => setLength(l)}
                >
                  {l}
                </button>
              ))}
            </div>
          </label>

          <div className="wizard-foot">
            <button type="button" className="ghost-btn">Back</button>
            <button type="button" className="primary-btn">
              <Icon name="sparkle" size={11} /> Draft outline
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
