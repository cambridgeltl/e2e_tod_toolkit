// Chatbox.js
// ----------------------------------------------------------------------------------------
// Description: This file contains the Chatbox component for handling chat interactions
//              between the user and the system. It includes functionalities for sending
//              and receiving messages, evaluating system responses at utterance level,
//              and maintaining chat history.
//              The component is written in javascript because the chatui package does
//              natively support typescript.
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import React, { useContext, useEffect, useState, useRef } from "react";
import "@chatui/core/es/styles/index.less";
import Chat, { Bubble, useMessages } from "@chatui/core";

import "@chatui/core/dist/index.css";
import { DialogueHistoryContext } from "./Assignment";
import { Alert, Button, Form, Input, Modal, Rate, Select } from "antd";
import { utt_issue_options, system_welcome_message } from "./configs";
import useToken from "./service/TokenService";
import io from "socket.io-client";
import {serverUrl} from "./configs"

const { TextArea } = Input;

// Initial messages in the chat
const initialMessages = [
  {
    type: "text",
    position: "left",
    content: { text: system_welcome_message, idx: 0 },
    speaker: "system",
  },
];

const Chatbox = () => {
  const dialogueHistory = useContext(DialogueHistoryContext);
  const { messages, appendMsg, setTyping } = useMessages(initialMessages);
  const [waitingMsg, setWaitingMsg] = useState(false);
  const [openModal, setOpenModal] = useState(false);
  const [clickedMessage, setClickedMessage] = useState(initialMessages[0]);
  const [utt_form] = Form.useForm();
  const [uttEvalList, setUttEvalList] = useState([]);
  const { token } = useToken();
  const [socket, setSocket] = useState(null);
  const idx_counter = useRef(1);

  // Function to handle modal close
  function handleClose() {
    setOpenModal(false);
  }

  // Function to handle form submission on evaluating a message
  function onFinish(values) {
    const new_dic = { ...values, idx: clickedMessage.content.idx };
    setUttEvalList((prevList) => [...prevList, new_dic]);
    utt_form.resetFields();
    setOpenModal(false);
  }

  // Establishing socket connection and handling incoming messages
  useEffect(() => {

    const newSocket = io(serverUrl, {
      transports: ["websocket", "polling"],
      reconnectionDelayMax: 5000,
      auth: {
        token: token, // Ensure the token is correctly formatted
      }
    });


    newSocket.on("system_message", (data) => {
      setWaitingMsg(false);
      appendMsg({
        type: "text",
        content: { text: data, idx: idx_counter.current},
        position: "left",
        speaker: "system",
      });
      console.log(idx_counter.current)
      idx_counter.current++;
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [token, appendMsg]);

  // Effect for managing typing state
  useEffect(() => {
    setTyping(waitingMsg);
  }, [waitingMsg]);

  // Updating dialogue history context
  useEffect(() => {
    const idxEvalDic = uttEvalList.reduce((acc, cur) => {
      acc[cur.idx] = cur;
      return acc;
    }, {});

    const utts = messages.map((i) => {
      const evaluation = i.speaker === "system" ? idxEvalDic[i.content.idx] : null;

      return { utterance: i.content, speaker: i.speaker, evaluation };
    });

    dialogueHistory.setDialogueHistory(utts);
  }, [messages, uttEvalList]);

  // Function to handle modal cancel
  const handleCancel = () => {
    utt_form.resetFields();
    setOpenModal(false);
  };

  // Function to handle sending messages
  function handleSend(type, val) {
    if (type === "text" && val.trim()) {
      appendMsg({
        type: "text",
        content: { text: val},
        position: "right",
        speaker: "user",
      });
      setWaitingMsg(true);
      socket.emit("user_message", val);
    }
  }

  // Function to render individual message content
  function renderMessageContent(msg) {
    const { content } = msg;
    return (
      <Bubble
        onClick={() => {
          if (msg.speaker === "system") {
            setClickedMessage(msg);
            setOpenModal(true);
          }
        }}
        content={content.text}
      />
    );
  }

  return (
    <div style={{ height: 600 }}>
      <Modal
        centered
        open={openModal}
        onCancel={() => handleClose()}
        width={800}
        footer={[
          <Button
            form="utterance_evaluation"
            key="submit"
            htmlType="submit"
            type={"primary"}
          >
            Submit
          </Button>,
        ]}
      >
        <Form
          form={utt_form}
          id="utterance_evaluation"
          layout="vertical"
          autoComplete="off"
          onFinish={(x) => onFinish(x)}
          onCancel={(x) => handleCancel(x)}
          initialValues={{
            ["issue"]: [],
            ["correction"]: clickedMessage.content.text,
          }}
        >
          <p style={{ font: "20" }}>
            Please evaluate the following system response.
          </p>
          <Alert message={clickedMessage.content.text} />
          <br />
          <Form.Item
            label="What is your overall satisfaction of this response."
            name="overall"
            required={true}
            rules={[{ required: true, message: "Please rate the response!" }]}
          >
            <Rate />
          </Form.Item>

          <Form.Item
            label="What issues are there in this response."
            name="issue"
            rules={[
              {
                required: true,
                message:
                  "Please tell us if this response has any of the following issues!",
              },
            ]}
          >
            <Select
              mode="multiple"
              allowClear
              style={{ width: "100%" }}
              placeholder="Please select"
              options={utt_issue_options}
            />
          </Form.Item>

          <Form.Item
            label="Could you correct the system response accordingly."
            name="correction"
            required={true}
          >
            <TextArea autoSize />
          </Form.Item>
        </Form>
      </Modal>

      <Chat
        locale="en-US"
        placeholder="Please type here..."
        navbar={{ title: "System" }}
        messages={messages}
        renderMessageContent={renderMessageContent}
        onSend={handleSend}
      />
    </div>
  );
};

export default Chatbox;
