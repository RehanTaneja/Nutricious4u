import 'react-native-gesture-handler';
// Limit how far the phone's text-size setting can enlarge text (see utils/fontScaling.ts)
import './utils/fontScaling';
import { registerRootComponent } from 'expo';

import App from './App';

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
