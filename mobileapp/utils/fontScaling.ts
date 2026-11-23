// Limits how much the phone's text-size setting can enlarge text in this app.
//
// Text still grows with the user's setting, but never past MAX_FONT_SIZE_MULTIPLIER
// times its normal size, so screens and popups keep fitting on small phones.
// A component that sets maxFontSizeMultiplier itself keeps its own value.
//
// React 19 ignores defaultProps on function components, so the default is applied by
// wrapping the render function of React Native's Text and TextInput (both forwardRef
// components). Loaded once from index.js, before the app renders.
import { Text, TextInput } from 'react-native';

export const MAX_FONT_SIZE_MULTIPLIER = 1.3;

function capFontScaling(component: any) {
  if (!component || typeof component.render !== 'function' || component.__fontScaleCapped) return;
  const render = component.render;
  component.render = (props: any, ref: any) =>
    render(
      props && props.maxFontSizeMultiplier === undefined
        ? { ...props, maxFontSizeMultiplier: MAX_FONT_SIZE_MULTIPLIER }
        : props,
      ref,
    );
  component.__fontScaleCapped = true;
}

capFontScaling(Text);
capFontScaling(TextInput);
