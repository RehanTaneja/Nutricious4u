/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const {setGlobalOptions} = require("firebase-functions");
// Removed unused onRequest and logger imports

setGlobalOptions({maxInstances: 10});

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const {Expo} = require("expo-server-sdk");

admin.initializeApp();
const expo = new Expo();

/**
 * Sends a push notification using Expo.
 * @param {string} expoPushToken
 * @param {string} title
 * @param {string} body
 */
async function sendPushNotification(expoPushToken, title, body) {
  if (!Expo.isExpoPushToken(expoPushToken)) {
    console.error(
        `Push token ${expoPushToken} is not a valid Expo push token`,
    );
    return;
  }
  const messages = [
      {
        to: expoPushToken,
        sound: "default",
        title,
        body,
        data: {},
      },
    ];
  await expo.sendPushNotificationsAsync(
    messages
  );
}

// TODO: Replace with your actual dietician user ID
const DIETICIAN_USER_ID = "DIETICIAN_USER_ID";

// 1. On new chat message
exports.onNewMessage = functions.firestore
    .document("chats/{chatUserId}/messages/{messageId}")
    .onCreate(async (snap, context) => {
      const message = snap.data();
      const chatUserId = context.params.chatUserId;
      const sender = message.sender;

      // Determine recipient: if sender is 'dietician', recipient is user, else recipient is dietician
      let recipientId;
      let title;
      let body;
      if (sender === "dietician") {
        recipientId = chatUserId;
        title = "New message from your dietician";
        body = message.text;
      } else {
        recipientId = DIETICIAN_USER_ID;
        title = "New message from a user";
        body = message.text;
      }

      // Get recipient's push token
      const userDoc = await admin
          .firestore()
          .collection("user_profiles")
          .doc(recipientId)
          .get();
      const expoPushToken = userDoc.get("expoPushToken");
      if (expoPushToken) {
        await sendPushNotification(expoPushToken, title, body);
      }
    });

// 2. On appointment scheduled/canceled - DISABLED to prevent duplicate notifications
// The frontend already handles appointment notifications via local scheduling
// exports.onAppointmentChange = functions.firestore
//     .document("appointments/{appointmentId}")
//     .onWrite(async (change, context) => {
//     // Only notify on create or delete
//       const appointment = change.after.exists ?
//       change.after.data() :
//       change.before.data();
//       const isCreated = change.after.exists && !change.before.exists;
//       const isDeleted = !change.after.exists && change.before.exists;

//       // Get dietician's push token
//       const dieticianDoc = await admin
//           .firestore()
//           .collection("user_profiles")
//           .doc(DIETICIAN_USER_ID)
//           .get();
//       const expoPushToken = dieticianDoc.get("expoPushToken");

//       if (expoPushToken) {
//         let title;
//         let body;
//         if (isCreated) {
//           title = "New Appointment Scheduled";
//           body =
//           `${appointment.userName} scheduled an appointment for ` +
//           `${appointment.date} at ${appointment.timeSlot}`;
//         } else if (isDeleted) {
//           title = "Appointment Cancelled";
//           body =
//           `${appointment.userName} cancelled their appointment for ` +
//           `${appointment.date} at ${appointment.timeSlot}`;
//         }
//         if (title && body) {
//           await sendPushNotification(expoPushToken, title, body);
//         }
//       }
//     });

// 3. On break added: cancel overlapping appointments and notify users
exports.onBreakAdded = functions.firestore
    .document("breaks/{breakId}")
    .onCreate(async (snap, context) => {
      const breakData = snap.data();
      const {fromTime, toTime, specificDate} = breakData;

      // Find overlapping appointments
      let appointmentsQuery = admin.firestore().collection("appointments");
      if (specificDate) {
        appointmentsQuery = appointmentsQuery.where(
            "date",
            "==",
            new Date(specificDate).toISOString().split("T")[0],
        );
      }
      const appointmentsSnapshot = await appointmentsQuery.get();

      const overlappingAppointments = [];
      appointmentsSnapshot.forEach((doc) => {
        const appt = doc.data();
        // Check if appointment timeSlot is within break
        if (appt.timeSlot >= fromTime && appt.timeSlot <= toTime) {
          overlappingAppointments.push({id: doc.id, ...appt});
        }
      });

      // Cancel appointments and notify users
      for (const appt of overlappingAppointments) {
        await admin
            .firestore()
            .collection("appointments")
            .doc(appt.id)
            .delete();
        // Notify user
        const userDoc = await admin
            .firestore()
            .collection("user_profiles")
            .doc(appt.userId)
            .get();
        const expoPushToken = userDoc.get("expoPushToken");
        if (expoPushToken) {
          await sendPushNotification(
              expoPushToken,
              "Appointment Cancelled",
              "Your appointment was cancelled because your dietician " +
            "added a break at that time.",
          );
        }
      }
    });
