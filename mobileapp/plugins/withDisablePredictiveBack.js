// Targeting Android 16 (API 36) turns on the predictive back gesture by default,
// which stops Android from calling Activity.onBackPressed(). React Native 0.79's
// ReactActivity still relies on onBackPressed() to route the back button to JS
// (React Navigation), so without this the back button/gesture would close the app
// instead of going back a screen. Remove once on a React Native version that
// handles OnBackInvokedCallback (Expo SDK 54+ manages this itself).
const { withAndroidManifest } = require('expo/config-plugins');

module.exports = function withDisablePredictiveBack(config) {
  return withAndroidManifest(config, (config) => {
    const application = config.modResults.manifest.application?.[0];
    if (application) {
      application.$['android:enableOnBackInvokedCallback'] = 'false';
    }
    return config;
  });
};
