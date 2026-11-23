// Single home for date/time logic in the app.
//
// - Server dates are ISO strings in UTC, usually without a timezone suffix
//   ("2026-11-22T10:15:30.123456"). parseServerDate reads them as UTC.
// - Appointment slots are on the dietician's clock (DIETICIAN_TIMEZONE), whatever
//   timezone the user's phone is in.
// - Daily diet reminders stay on the phone's own clock and do not use this file.

/** The dietician's timezone. Appointment slots ("10:00") are times on this clock. */
export const DIETICIAN_TIMEZONE = 'Asia/Kolkata';
/** Used only if the phone cannot do timezone conversions (no Intl timezone support). */
const DIETICIAN_FALLBACK_OFFSET_MINUTES = 330;

const HAS_TZ_SUFFIX = /(?:Z|[+\-]\d{2}:?\d{2})$/i;
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const validDate = (d: Date): Date | null => (isNaN(d.getTime()) ? null : d);
const pad2 = (n: number) => String(n).padStart(2, '0');

/**
 * Read a date sent by the server. Strings without a timezone are UTC; strings with
 * "Z" or an offset are kept as they are; fractional seconds are cut to milliseconds.
 * Also accepts Date, epoch milliseconds and Firestore Timestamps. Returns null if invalid.
 */
export function parseServerDate(value: any): Date | null {
  if (value === null || value === undefined || value === '') return null;
  if (value instanceof Date) return validDate(value);
  if (typeof value === 'number') return validDate(new Date(value));
  if (typeof value === 'object') {
    if (typeof value.toDate === 'function') return validDate(value.toDate());
    if (typeof value.seconds === 'number') {
      return validDate(new Date(value.seconds * 1000 + Math.floor((value.nanoseconds || 0) / 1e6)));
    }
    return null;
  }
  if (typeof value !== 'string') return null;
  let s = value.trim().replace(/^(\d{4}-\d{2}-\d{2}) (?=\d)/, '$1T').replace(/(\.\d{3})\d+/, '$1');
  if (s.includes('T') && !HAS_TZ_SUFFIX.test(s)) s += 'Z';
  return validDate(new Date(s));
}

/** Format a server date for display on the phone's clock; '' if it is missing/invalid. */
export function formatServerDate(value: any, locale?: string, options?: Intl.DateTimeFormatOptions): string {
  const d = parseServerDate(value);
  return d ? d.toLocaleDateString(locale, options) : '';
}

/** The phone's timezone: IANA name (null if unavailable) and minutes east of UTC. */
export function deviceTimezone(): { timezone: string | null; utcOffsetMinutes: number } {
  let timezone: string | null = null;
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    timezone = typeof tz === 'string' && tz.length > 0 ? tz : null;
  } catch {
    timezone = null;
  }
  return { timezone, utcOffsetMinutes: -new Date().getTimezoneOffset() };
}

// ---------------------------------------------------------------------------------
// Calendars in a given timezone (the dietician's)

export type ZonedParts = { year: number; month: number; day: number; hour: number; minute: number; second: number };

const formatterCache: Record<string, Intl.DateTimeFormat | null> = {};
function partsFormatter(tz: string): Intl.DateTimeFormat | null {
  if (tz in formatterCache) return formatterCache[tz];
  let f: Intl.DateTimeFormat | null = null;
  try {
    f = new Intl.DateTimeFormat('en-US', {
      timeZone: tz, hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
    // Check it really converts (some engines ignore timeZone)
    if (typeof (f as any).formatToParts !== 'function') f = null;
  } catch {
    f = null;
  }
  formatterCache[tz] = f;
  return f;
}

function fallbackOffsetMinutes(tz: string, date: Date): number {
  return tz === DIETICIAN_TIMEZONE ? DIETICIAN_FALLBACK_OFFSET_MINUTES : -date.getTimezoneOffset();
}

function partsFromShift(date: Date, offsetMinutes: number): ZonedParts {
  const s = new Date(date.getTime() + offsetMinutes * 60000);
  return {
    year: s.getUTCFullYear(), month: s.getUTCMonth() + 1, day: s.getUTCDate(),
    hour: s.getUTCHours(), minute: s.getUTCMinutes(), second: s.getUTCSeconds(),
  };
}

/** Wall-clock parts of a moment in a timezone. */
export function zonedParts(date: Date, tz: string): ZonedParts {
  const f = partsFormatter(tz);
  if (f) {
    try {
      const p: Record<string, number> = {};
      for (const part of (f as any).formatToParts(date)) {
        if (part.type !== 'literal') p[part.type] = parseInt(part.value, 10);
      }
      if (p.year && p.month && p.day && !isNaN(p.hour) && !isNaN(p.minute)) {
        return { year: p.year, month: p.month, day: p.day, hour: p.hour % 24, minute: p.minute, second: p.second || 0 };
      }
    } catch {
      // fall through
    }
  }
  return partsFromShift(date, fallbackOffsetMinutes(tz, date));
}

/** Minutes east of UTC for a timezone at a given moment. */
export function zoneOffsetMinutes(date: Date, tz: string): number {
  const p = zonedParts(date, tz);
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return Math.round((asUtc - Math.floor(date.getTime() / 1000) * 1000) / 60000);
}

/** The moment when a timezone's clock shows the given wall time (month is 1-12; day may overflow). */
export function zonedWallTimeToDate(year: number, month: number, day: number, hour: number, minute: number, tz: string): Date {
  const guess = Date.UTC(year, month - 1, day, hour, minute);
  let result = guess - zoneOffsetMinutes(new Date(guess), tz) * 60000;
  const corrected = guess - zoneOffsetMinutes(new Date(result), tz) * 60000; // daylight-saving edge
  if (corrected !== result) result = corrected;
  return new Date(result);
}

/** Calendar day of a moment in a timezone, in the same format as Date.toDateString() ("Mon Nov 23 2026"). */
export function zonedDateKey(date: Date, tz: string): string {
  const p = zonedParts(date, tz);
  const weekday = new Date(Date.UTC(p.year, p.month - 1, p.day)).getUTCDay();
  return `${WEEKDAYS[weekday]} ${MONTHS[p.month - 1]} ${pad2(p.day)} ${p.year}`;
}

/** Format a moment on a timezone's clock. */
export function formatInZone(date: Date, tz: string, options: Intl.DateTimeFormatOptions, locale: string = 'en-US'): string {
  if (partsFormatter(tz)) {
    try {
      return date.toLocaleString(locale, { ...options, timeZone: tz });
    } catch {
      // fall through
    }
  }
  // No timezone support: shift so the phone's own clock shows the zone's wall time
  const shifted = new Date(date.getTime() + (fallbackOffsetMinutes(tz, date) + date.getTimezoneOffset()) * 60000);
  return shifted.toLocaleString(locale, options);
}

// ---------------------------------------------------------------------------------
// Appointments: slots are on the dietician's clock

/** Calendar day (toDateString format) on the dietician's clock. */
export const dieticianDateKey = (date: Date): string => zonedDateKey(date, DIETICIAN_TIMEZONE);

/** The next `count` days on the dietician's calendar, each as noon of that day. */
export function dieticianWeekDates(count: number = 7, now: Date = new Date()): Date[] {
  const p = zonedParts(now, DIETICIAN_TIMEZONE);
  const dates: Date[] = [];
  for (let i = 0; i < count; i++) dates.push(zonedWallTimeToDate(p.year, p.month, p.day + i, 12, 0, DIETICIAN_TIMEZONE));
  return dates;
}

/** The moment a slot label ("10:00") starts on the dietician's calendar day containing `day`. */
export function dieticianSlotDate(day: Date, timeSlot: string): Date {
  const p = zonedParts(day, DIETICIAN_TIMEZONE);
  const [h, m] = timeSlot.split(':').map(x => parseInt(x, 10));
  return zonedWallTimeToDate(p.year, p.month, p.day, h || 0, m || 0, DIETICIAN_TIMEZONE);
}

/** True when the phone's clock differs from the dietician's at that moment. */
export function phoneDiffersFromDietician(date: Date = new Date()): boolean {
  return zoneOffsetMinutes(date, DIETICIAN_TIMEZONE) !== -date.getTimezoneOffset();
}

/** Short date on the dietician's calendar, e.g. "Mon, Nov 23". */
export const formatDieticianDay = (date: Date): string =>
  formatInZone(date, DIETICIAN_TIMEZONE, { weekday: 'short', month: 'short', day: 'numeric' });

/** A slot's time on the phone's clock, e.g. "08:30" (24-hour, short enough for grid cells). */
export const formatPhoneTime24 = (date: Date): string => `${pad2(date.getHours())}:${pad2(date.getMinutes())}`;

/** A slot's moment on the phone's clock with its day, e.g. "Sun, Nov 22, 8:30 PM". */
export const formatPhoneDateTime = (date: Date): string =>
  date.toLocaleString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });

/** " (Sun, Nov 22, 8:30 PM your time)" when the phone is in another timezone, else ''. */
export function localTimeSuffix(slotDate: Date): string {
  return phoneDiffersFromDietician(slotDate) ? ` (${formatPhoneDateTime(slotDate)} your time)` : '';
}
