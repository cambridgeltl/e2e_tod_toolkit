// configs.js
// ----------------------------------------------------------------------------------------
// Description: Configuration file for the React application.
//
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

export const serverUrl = process.env.REACT_APP_SERVER_URL || 'http://127.0.0.1:80';
export const clientUrl = process.env.REACT_APP_CLIENT_URL || 'http://127.0.0.1:3000';

export const target_language = "English"
export const contact_name = "Songbo Hu"
export const contact_address = "University of Cambridge"
export const contact_email = "sh2091@cam.ac.uk"

export const system_welcome_message = "Hello, welcome to the digital assistant system. You can query information about attraction, restaurant, hotels, taxi, hospital, and police."

export const  utt_issue_options = [{label: "grammatically incorrect", value : "ungrammatical"}, {label: "off-topic", value : "irrelevant"},
    {label: "too generic", value : "notinformative"}, {label: "not engaging", value : "notengaging"}, {label: "produce contradicting information", value : "notconsistent"},
    {label: "offensive", value : "offensive"}, {label: "none of the list", value : "no"}]


export const  dial_eval_options = [{label: "maintaining a good conversation flow", value : "coherence"},
    {label: "able to recover from errors", value : "errorrecovery"},
    {label: "consistent in the information", value : "consistency"},
    {label: "provide diverse responses", value : "diversity"},
    {label: "display likeable personality", value : "likeability"},
    {label: "understand the user", value : "understanding"},
    {label: "provide unique and non-generic information", value : "informativeness"},
    {label: "actively ask the user questions", value : "inquisitiveness"},
    {label: "none of the list", value : "no"},
]