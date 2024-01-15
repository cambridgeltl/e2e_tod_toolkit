// Admin.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the Admin component for managing user access controls
//              and downloading submission and user data.
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import React, {useEffect, useState} from "react";
import {Alert, Button, Collapse, Form, Layout, message, Switch, Transfer} from 'antd';
import {NavigateFunction, useNavigate} from "react-router-dom";
import type {TransferDirection} from 'antd/es/transfer';
import useToken from "./service/TokenService";
import { serverUrl } from "./configs";

const {Header, Content, Footer} = Layout;

// Type definitions for user and access control data
interface RecordType {
    key: string;
    email: string;
    is_authorised: boolean;
}

interface UserDataType {
    name: string;
    email: string;
    id: string;
    country: string;
    role: string;
}


type AccessFieldType = {
    allowed_list: string[];
    has_access_control: boolean;
};


// Processes the user list for display in the Transfer component
function process_user_list_to_show(user_list: UserDataType[]){
    return user_list
        .filter(user => user.role !== 'admin') // Exclude users with 'admin' role
        .map(user => {
            return {
                key: user.id,
                email: user.email,
                is_authorised: user.role === 'authorised_user' // Set 'is_authorised' for 'authorised_user' role
            };
        })
}

// Fetches user list from the server and updates state
function getUserList(token: string | null, setUserListTransferData: {
        (value: React.SetStateAction<RecordType[]>): void; (arg0: {
            key: string; email: string; is_authorised: boolean; // Set 'is_authorised' for 'authorised_user' role
        }[]): void;
    }, setEnabled: { (value: React.SetStateAction<boolean>): void; (arg0: any): void; }) {

    if (!token) {
        console.error("No token available for authorization");
        return;
    }


    fetch(serverUrl+'/api/get_all_users', { // Update with your server URL
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.user_list) {

                let record_list = process_user_list_to_show(data.user_list)
                setUserListTransferData(record_list)
                setEnabled(data.access_control_enabled)

            } else {
                console.error('Failed to fetch user list data:', data.msg);
            }
        })
        .catch(error => {
            console.error('Error fetching task data:', error);
        });
}

// Downloads submission data from the server
function downloadSubmissionData(token: string | null) {

    fetch(serverUrl + '/api/get_all_results', { // Replace with your actual endpoint
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            // Assuming data is of the format { success: boolean; data: any; }
            if(data.success) {
                const fileData = JSON.stringify(data.data);
                const blob = new Blob([fileData], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'submitted_data.json';
                link.click();
                URL.revokeObjectURL(url);
            } else {
                message.error('Failed to download data.');
            }
        })
        .catch(error => {
            console.error('Error downloading data:', error);
            message.error('Error downloading data.');
        });
}

// Downloads all user data from the server
function downloadAllUserData(token: string | null) {
    fetch(serverUrl + '/api/get_all_users', { // Replace with your actual endpoint
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.user_list) {
                const fileData = JSON.stringify(data.user_list);
                const blob = new Blob([fileData], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'user_data.json';
                link.click();
                URL.revokeObjectURL(url);
            } else {
                message.error('Failed to download user data.');
            }
        })
        .catch(error => {
            console.error('Error downloading user data:', error);
            message.error('Error downloading user data.');
        });
}

// Handles form submission failure
function onFinishFailed(errorInfo:any){
    console.log('Failed:', errorInfo);
    message.error('Failed to log in.');
}


const Admin: React.FC = () => {
    const navigate = useNavigate();
    const [targetKeys, setTargetKeys] = useState<string[]>([]);
    const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
    const [enabled, setEnabled] = useState(false);
    const [userListTransferData, setUserListTransferData] = useState<RecordType[]>([]);
    const { token, removeToken, setToken, getUserRole, getUserPermissions } = useToken();

    useEffect(() =>{
        getUserList(token, setUserListTransferData, setEnabled)
    }, [])

    useEffect(() => {

        let targetKeys = userListTransferData.filter((item) => item.is_authorised).map((item) => item.key);
        setTargetKeys(targetKeys)

    }, [userListTransferData])


    useEffect(() => {
        // Check if the user role is admin
        const userPermissions = getUserPermissions();
        console.log("userPermissions")
        console.log(userPermissions)
        if (!userPermissions.includes("visit_admin_page")) {
            message.warning('Access Denied. Redirecting to home page.');
            navigate('/'); // Redirect to the root page
        }
    }, [navigate, getUserRole]);

    function onFinish() {

        // Include the targetKeys in the submission data
        const submissionData = {
            allowed_list: targetKeys, // This assumes targetKeys is accessible here
            has_access_control: enabled
        };

        console.log("Submission Data:", submissionData);

        // Here, you'll need to replace with your API endpoint and handle the actual submission
        fetch(serverUrl+'/api/submit_access_control', { // Replace with your actual endpoint
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token, // Ensure the token is accessible
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(submissionData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    message.success('Access control settings updated successfully.');
                    // navigate('/some-route'); // Navigate to another page if needed
                } else {
                    console.error('Failed to update access control settings:', data.msg);
                    message.error('Failed to update access control settings.');
                }
            })
            .catch(error => {
                console.error('Error updating access control settings:', error);
                message.error('Error updating access control settings.');
            });
    }

    const handleChange = (
        newTargetKeys: string[],
        direction: TransferDirection,
        moveKeys: string[],
    ) => {
        setTargetKeys(newTargetKeys);

        console.log('targetKeys: ', newTargetKeys);
        console.log('direction: ', direction);
        console.log('moveKeys: ', moveKeys);
    };

    const handleSelectChange = (sourceSelectedKeys: string[], targetSelectedKeys: string[]) => {
        setSelectedKeys([...sourceSelectedKeys, ...targetSelectedKeys]);

        console.log('sourceSelectedKeys: ', sourceSelectedKeys);
        console.log('targetSelectedKeys: ', targetSelectedKeys);
    };

    const handleScroll = (
        direction: TransferDirection,
        e: React.SyntheticEvent<HTMLUListElement, Event>,
    ) => {
        console.log('direction:', direction);
        console.log('target:', e.target);
    };

    const handleEnable = (checked: boolean) => {
        setEnabled(checked);
    };

    function access_info_panel() {
        if (enabled) {
            return (
            <Alert
                message="Access Control Enabled"
                description="Only the authorised users listed below can participate in and do the task. If you want to modify the authorised users list, please adjust the following list and click submit. You may also change the disabled button below to disable the access control."
                type="warning"
                showIcon
            />)
        } else {
            return ( <Alert
                message="Access Control Disabled"
                description="Now, all the registered users can participate in and do the task. You may click the disabled button below and then the submit button to enable the access control."
                type="success"
                showIcon
            />)

        }
    }


    return(
            <Layout>
                <Header
                    style={{
                        backgroundColor:'#F5F5F5FF',
                        padding: 0,
                    }}
                >

                    <div style={{display: 'flex', justifyContent: 'center',    alignItems: 'center'}}>
                        <b>
                            Administration Page
                        </b>
                    </div>
                </Header>
                <Content className="site-layout">
                    <div>
                        <Collapse defaultActiveKey={['1','2']}>
                            <Collapse.Panel header="Access Control" key="1" >

                                {access_info_panel()}
                                <br/>

                                <Form
                                    name="access_control"
                                    style={{ maxWidth: 800 }}
                                    initialValues={{ remember: true }}
                                    onFinish={(x) => onFinish()}
                                    onFinishFailed={onFinishFailed}
                                    autoComplete="off"
                                >


                                    <Form.Item<AccessFieldType>
                                        name="allowed_list"
                                        rules={[]}
                                    >
                                        <Transfer
                                            dataSource={userListTransferData}
                                            titles={['Normal', 'Authorised']}
                                            targetKeys={targetKeys}
                                            selectedKeys={selectedKeys}
                                            onChange={handleChange}
                                            onSelectChange={handleSelectChange}
                                            onScroll={handleScroll}
                                            render={(item) => item.email}
                                            disabled={!enabled}
                                            oneWay
                                            showSearch
                                            listStyle={{
                                                width: 250,
                                                height: 300,
                                            }}
                                            style={{ marginBottom: 16 }}
                                        />
                                        <Switch
                                            unCheckedChildren="disabled"
                                            checkedChildren="Enabled"
                                            checked={enabled}
                                            onChange={handleEnable}
                                        />
                                    </Form.Item>

                                    <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                        <Button type="primary" htmlType="submit">
                                            Submit
                                        </Button>
                                    </Form.Item>
                                </Form>



                            </Collapse.Panel>


                            <Collapse.Panel header="Download Data" key="2">

                                <Button onClick={() => downloadSubmissionData(token)} type="primary" style={{ marginRight: 10 }}>
                                    Download Submitted Data
                                </Button>

                                <Button onClick={() => downloadAllUserData(token)} type="primary" style={{ marginRight: 10 }}>
                                    Download User Information
                                </Button>
                            </Collapse.Panel>
                        </Collapse>
                    </div>

                </Content>
                <Footer style={{ textAlign: 'center', backgroundColor:'#F5F5F5FF' }}>Cambridge LTL ©2023</Footer>
            </Layout>
        )
}


export default Admin;
