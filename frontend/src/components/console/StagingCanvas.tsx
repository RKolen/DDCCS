import * as React from 'react';
import {
  depthRanks, FAR_DEPTH, HIDDEN_WARNING, hiddenFractions, LIMB_BOTTOM,
  LIMB_REACH, LIMB_TOP, NEAR_DEPTH, type StageLimb, type StagePlacement,
} from '../../utils/storyImage';

/**
 * The pre-render staging: place the cast before paying for a scene.
 *
 * A render costs minutes and a ComfyUI restart, and the thing that decides
 * whether it reads as a scene or a line-up is where people stand.
 *
 * Click a figure and use the arrow keys: left and right move across the
 * frame, up moves further back and down brings them towards the camera.
 * Dragging works too, but it is the coarse tool - the keys are the one that
 * can put somebody exactly where you want them.
 *
 * The client's vertical mapping is deliberately approximate. The server owns
 * the perspective maths and returns the real boxes with each preview, so what
 * is drawn here is always what the renderer will use rather than a
 * reimplementation of it that can drift.
 *
 * Lateral position is the exception, and it has to be: a handle placed from
 * the last response alone does not move until the server answers, so moving
 * anyone sideways looked like it did nothing. Where a figure sits across the
 * frame is the one part of the layout the client can compute exactly - the
 * renderer centres the box on `lateral` and nothing else - so the handle
 * follows immediately and only its size waits on the server.
 *
 * A picked figure shows its joints. Drag one, or focus it and use the arrow
 * keys, to move that limb; the move is kept in the figure's own units, so it
 * stays put when the figure is walked further back.
 */

interface Props {
  /** Everyone in the shot, in cast order. */
  people: Array<{ name: string; characterId: string }>;
  /** Shot type, which sets how much of the frame a figure fills. */
  shot: string;
  /** Current staging, one row per person. */
  placements: StagePlacement[];
  /** Called with the new staging whenever a figure moves. */
  onChange: (placements: StagePlacement[]) => void;
}

interface Preview {
  imageBase64: string;
  width:       number;
  height:      number;
  boxes:       Map<string, number[]>;
  skeletons:   Map<string, StageLimb[]>;
}

/** Where a drag started, so it moves by how far the pointer went. */
interface Grab {
  x:       number;
  y:       number;
  lateral: number;
  depth:   number;
}

/** Arrow-key steps. Shift multiplies them for crossing the frame quickly. */
const LATERAL_STEP = 0.01;
const DEPTH_STEP = 0.05;
const COARSE = 5;

/** Arrow-key step for a picked joint, in the figure's layout units. */
const LIMB_STEP = 0.01;

/** How long to wait for more input before asking the server to redraw. */
const REDRAW_IDLE_MS = 250;

/** Vertical travel is depth: the top of the frame is as far back as it goes. */
function depthFromFraction(fraction: number): number {
  const held = Math.min(Math.max(fraction, 0), 1);
  return NEAR_DEPTH + (FAR_DEPTH - NEAR_DEPTH) * (1 - held);
}

function fractionFromDepth(depth: number): number {
  return 1 - (depth - NEAR_DEPTH) / (FAR_DEPTH - NEAR_DEPTH);
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

/** "r_wrist" -> "right wrist". The character's own right, not the viewer's. */
function jointLabel(joint: string): string {
  return joint.replace(/^r_/, 'right ').replace(/^l_/, 'left ');
}

/**
 * Where each draggable joint is: the operator's move when there is one, the
 * drawn skeleton otherwise. The move wins so a dragged joint follows the
 * pointer instead of waiting for the redraw.
 */
function jointsOf(row: StagePlacement, skeleton: StageLimb[]): StageLimb[] {
  const moved = new Map((row.limbs ?? []).map(limb => [limb.joint, limb]));
  return skeleton.map(limb => moved.get(limb.joint) ?? limb);
}

export default function StagingCanvas({
  people, shot, placements, onChange,
}: Props): React.ReactElement {
  const [preview, setPreview] = React.useState<Preview | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [dragging, setDragging] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<string | null>(null);
  const frame = React.useRef<HTMLDivElement | null>(null);
  const grab = React.useRef<Grab | null>(null);
  const [limbDrag, setLimbDrag] = React.useState<string | null>(null);
  const [pickedJoint, setPickedJoint] = React.useState<string | null>(null);
  const idle = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = React.useCallback(async (rows: StagePlacement[]) => {
    setBusy(true);
    try {
      const res = await fetch('/api/stage-preview', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          people: people.map(person => ({ name: person.name })),
          placements: rows,
          shot,
        }),
      });
      if (!res.ok) {
        setError((await res.json())?.error ?? 'Could not draw the staging.');
        return;
      }
      const data = await res.json();
      setError(null);
      setPreview({
        imageBase64: data.image_base64,
        width:       data.width,
        height:      data.height,
        boxes: new Map<string, number[]>(
          (data.placements ?? []).map((row: StagePlacement) =>
            [row.name, row.box ?? []] as [string, number[]]),
        ),
        skeletons: new Map<string, StageLimb[]>(
          (data.placements ?? []).map((row: StagePlacement) =>
            [row.name, row.skeleton ?? []] as [string, StageLimb[]]),
        ),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not draw the staging.');
    } finally {
      setBusy(false);
    }
  }, [people, shot]);

  /* Held keys and a dragged pointer both produce a stream of moves, and each
     redraw is a server round trip. Redrawing once the input stops keeps the
     figure sizes honest without a request per pixel. */
  const redrawWhenIdle = React.useCallback((rows: StagePlacement[]) => {
    if (idle.current !== null) clearTimeout(idle.current);
    idle.current = setTimeout(() => { void refresh(rows); }, REDRAW_IDLE_MS);
  }, [refresh]);

  React.useEffect(() => () => {
    if (idle.current !== null) clearTimeout(idle.current);
  }, []);

  /* Pose, facing and direction all change the skeleton, so the preview has
     to follow them or it shows a staging nobody asked for. Lateral and depth
     are deliberately absent: those redraw when the input goes idle, and
     watching them here would refetch on every pixel of a drag. */
  const stanceKey = placements
    .map(row => `${row.name}:${row.pose}:${row.facing}:${row.toward}`).join('|');
  React.useEffect(() => {
    if (people.length > 0) void refresh(placements);
    // Re-drawn when the cast, the shot or a stance changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [people.length, shot, stanceKey]);

  /**
   * Move one figure and schedule the redraw.
   *
   * @param name    Who is moving.
   * @param lateral Their new position across the frame.
   * @param depth   Their new distance from the camera.
   */
  const put = (name: string, lateral: number, depth: number): void => {
    const rows = placements.map(row => (
      row.name === name
        ? { ...row, lateral: clamp(lateral, 0, 1),
            depth: clamp(depth, NEAR_DEPTH, FAR_DEPTH) }
        : row
    ));
    onChange(rows);
    redrawWhenIdle(rows);
  };

  /**
   * Move one joint of one figure and schedule the redraw.
   *
   * @param name  Whose limb.
   * @param joint Which joint, e.g. "r_wrist".
   * @param x     Across, from the figure's centre, in layout units.
   * @param y     Down, from the top of the figure's box, in layout units.
   */
  const putLimb = (name: string, joint: string, x: number, y: number): void => {
    const limb = {
      joint, x: clamp(x, -LIMB_REACH, LIMB_REACH), y: clamp(y, LIMB_TOP, LIMB_BOTTOM),
    };
    const rows = placements.map(row => (
      row.name === name
        ? { ...row,
            limbs: [...(row.limbs ?? []).filter(held => held.joint !== joint), limb] }
        : row
    ));
    onChange(rows);
    redrawWhenIdle(rows);
  };

  const resetLimbs = (name: string): void => {
    const rows = placements.map(row => (row.name === name ? { ...row, limbs: [] } : row));
    onChange(rows);
    redrawWhenIdle(rows);
  };

  /* A joint goes to where the pointer is, unlike a figure: it is a point,
     so there is no grab offset for it to jump by. */
  const dragLimb = (event: React.PointerEvent, row: StagePlacement, joint: string): void => {
    const frameBox = frame.current?.getBoundingClientRect();
    const box = preview?.boxes.get(row.name) ?? [];
    if (frameBox == null || preview == null || box.length !== 4) return;
    const across = (event.clientX - frameBox.left) / frameBox.width;
    const down = ((event.clientY - frameBox.top) / frameBox.height) * preview.height;
    putLimb(row.name, joint,
      (across - row.lateral) / ((box[2] / preview.width) * 2),
      (down - box[1]) / box[3]);
  };

  const nudgeLimb = (event: React.KeyboardEvent, row: StagePlacement, limb: StageLimb): void => {
    const step = LIMB_STEP * (event.shiftKey ? COARSE : 1);
    const moves: Record<string, [number, number]> = {
      ArrowLeft: [-step, 0], ArrowRight: [step, 0],
      ArrowUp:   [0, -step], ArrowDown:  [0, step],
    };
    const move = moves[event.key];
    if (move === undefined) return;
    event.preventDefault();
    putLimb(row.name, limb.joint, limb.x + move[0], limb.y + move[1]);
  };

  /* By how far the pointer moved, never to where it is. Setting the figure
     to the pointer's own position threw it to a new distance the instant it
     was grabbed - press near the top of a tall handle and the character
     jumped to the back of the scene - and every wobble across a horizontal
     drag then resized them. */
  const drag = (event: React.PointerEvent, row: StagePlacement): void => {
    const box = frame.current?.getBoundingClientRect();
    const from = grab.current;
    if (box == null || from == null) return;
    const lateral = from.lateral + (event.clientX - from.x) / box.width;
    const travel = (event.clientY - from.y) / box.height;
    put(row.name, lateral, depthFromFraction(fractionFromDepth(from.depth) + travel));
  };

  const nudge = (event: React.KeyboardEvent, row: StagePlacement): void => {
    const step = event.shiftKey ? COARSE : 1;
    const moves: Record<string, [number, number]> = {
      ArrowLeft:  [-LATERAL_STEP * step, 0],
      ArrowRight: [LATERAL_STEP * step, 0],
      // Up is away from the camera, which is up the frame towards the horizon.
      ArrowUp:    [0, DEPTH_STEP * step],
      ArrowDown:  [0, -DEPTH_STEP * step],
    };
    const move = moves[event.key];
    if (move === undefined) return;
    event.preventDefault();
    put(row.name, row.lateral + move[0], row.depth + move[1]);
  };

  if (people.length === 0) {
    return <p className="story-image-likeness--none">Nobody is in the shot yet.</p>;
  }

  const scale = preview ? 1 / preview.width : 0;
  const ranks = depthRanks(placements);
  const hidden = preview ? hiddenFractions(preview.boxes, ranks) : new Map();
  // A figure can be staged perfectly and still never appear, because a
  // taller neighbour stands exactly where they do. Worth knowing before the
  // render rather than after it.
  const swallowed = [...hidden.entries()]
    .filter(([, covered]) => covered >= HIDDEN_WARNING)
    .map(([name, covered]) => `${name} is ${Math.round(covered * 100)}% hidden`);
  const held = placements.find(row => row.name === selected);
  const heldBox = held && preview ? preview.boxes.get(held.name) ?? [] : [];
  const heldJoints = held && preview
    ? jointsOf(held, preview.skeletons.get(held.name) ?? []) : [];

  return (
    <div className="staging">
      <div
        className="staging-frame"
        ref={frame}
        style={{ aspectRatio: preview ? `${preview.width} / ${preview.height}` : '3 / 2' }}
      >
        {preview && (
          <img
            src={`data:image/png;base64,${preview.imageBase64}`}
            alt="Where each character stands, drawn as skeletons"
            className="staging-skeleton"
          />
        )}
        {preview && placements.map(row => {
          const box = preview.boxes.get(row.name) ?? [];
          if (box.length !== 4) return null;
          const wide = box[2] * scale;
          const state = dragging === row.name ? ' staging-handle--held'
            : selected === row.name ? ' staging-handle--picked' : '';
          return (
            <button
              type="button"
              key={row.name}
              className={`staging-handle${state}`}
              aria-label={`${row.name}, number ${ranks.get(row.name)}`}
              style={{
                /* Centred on lateral, exactly as the renderer centres the
                   box, so this tracks the pointer instead of the response. */
                left:   `${(row.lateral - wide / 2) * 100}%`,
                top:    `${(box[1] / preview.height) * 100}%`,
                width:  `${wide * 100}%`,
                height: `${(box[3] / preview.height) * 100}%`,
              }}
              onPointerDown={event => {
                event.currentTarget.setPointerCapture(event.pointerId);
                grab.current = {
                  x: event.clientX, y: event.clientY,
                  lateral: row.lateral, depth: row.depth,
                };
                setDragging(row.name);
                setSelected(row.name);
                setPickedJoint(null);
              }}
              onPointerMove={event => { if (dragging === row.name) drag(event, row); }}
              onPointerUp={() => { setDragging(null); grab.current = null; }}
              onFocus={() => { setSelected(row.name); setPickedJoint(null); }}
              onKeyDown={event => nudge(event, row)}
            >
              <span className="staging-handle-name">
                <span className="staging-handle-rank">{ranks.get(row.name)}</span>
                {row.name}
              </span>
            </button>
          );
        })}
        {preview && held && heldBox.length === 4 && heldJoints.map(limb => (
          <button
            type="button"
            key={limb.joint}
            className={'staging-joint'
              + ((held.limbs ?? []).some(moved => moved.joint === limb.joint)
                ? ' staging-joint--moved' : '')
              + (pickedJoint === limb.joint ? ' staging-joint--picked' : '')}
            aria-label={`${held.name}, ${jointLabel(limb.joint)}`}
            title={jointLabel(limb.joint)}
            style={{
              left: `${(held.lateral + limb.x * (heldBox[2] / preview.width) * 2) * 100}%`,
              top:  `${((heldBox[1] + limb.y * heldBox[3]) / preview.height) * 100}%`,
            }}
            onPointerDown={event => {
              event.currentTarget.setPointerCapture(event.pointerId);
              setLimbDrag(limb.joint);
              setPickedJoint(limb.joint);
            }}
            onPointerMove={event => {
              if (limbDrag === limb.joint) dragLimb(event, held, limb.joint);
            }}
            onPointerUp={() => setLimbDrag(null)}
            onFocus={() => setPickedJoint(limb.joint)}
            onKeyDown={event => nudgeLimb(event, held, limb)}
          />
        ))}
      </div>
      {held && (held.limbs ?? []).length > 0 && (
        <button
          type="button"
          className="staging-limb-reset"
          onClick={() => resetLimbs(held.name)}
        >
          Reset {held.name}&apos;s limbs
        </button>
      )}
      {swallowed.length > 0 && (
        <p className="staging-warning">{swallowed.join('; ')}.</p>
      )}
      <p className="story-image-likeness--none">
        {error ?? (busy ? 'Drawing the staging...' : held && pickedJoint
          ? `${held.name}'s ${jointLabel(pickedJoint)}: drag it, or use the `
            + 'arrow keys, Shift for bigger steps. Changing their pose, facing '
            + 'or direction resets the limbs.'
          : held
          ? `${held.name}: across ${held.lateral.toFixed(2)}, `
            + `distance ${held.depth.toFixed(2)}. Arrow keys move them - up is `
            + 'further back, down is towards the camera, Shift for bigger steps.'
          : 'Click a figure, then use the arrow keys: left and right across the '
            + 'frame, up further back, down towards the camera. The number is '
            + 'front to back, and In front on the cast list sets it.')}
      </p>
    </div>
  );
}

export { depthFromFraction, fractionFromDepth };
