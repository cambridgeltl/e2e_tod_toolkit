// Register.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the Register component for handling user registration
//              in a dialogue evaluation experiment.
//
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import React from "react";
import {message, Input, Button, Collapse, Form, Layout, Select} from 'antd';
import {contact_address, serverUrl} from "./configs";
import {contact_name, contact_email} from "./configs";
import {NavigateFunction, useNavigate} from "react-router-dom";
import useToken from "./service/TokenService";

const {Header, Content, Footer} = Layout;
const { Option } = Select;

// Type definition for form fields
type RegistrationFieldType = {
    username: string;
    email: string;
    password: string;
    country: string;
};

// Function to handle form submission for registration
function onFinish(values: RegistrationFieldType, navigate: NavigateFunction, set_access_token: { (userToken: React.SetStateAction<string | null>): void; (arg0: string): void; }){

    console.log('Received values of form: ', values);

    fetch(serverUrl+'/api/register', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "username": values.username, "email" : values.email, "password" : values.password, "country": values.country})
    }).then(function (response) {
        console.log(response);
        return response.json();
    })
        .then(function (json) {
            if(json.success === false){
                message.error(json.msg);
            }else{
                console.log("access_token")
                console.log(json.access_token)
                set_access_token(json.access_token)
                navigate('/assignment');
            }

        })
        .catch((err) => {
            message.error('Bad request.');
        });


}

// Function to handle form submission failure
function onFinishFailed(errorInfo:any){
    console.log('Failed:', errorInfo);
}

const Register: React.FC = () => {
    const navigate = useNavigate();
    const { token, removeToken, setToken, getUserRole } = useToken();


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
                            Dialogue Evaluation Experiment
                        </b>
                    </div>

                </Header>

                <Content className="site-layout">
                    <div>
                        <Collapse defaultActiveKey={['1','2','3']}>
                            <Collapse.Panel header="Contact" key="1" >
                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}>
                                    {contact_name}
                                    <br/>
                                    {contact_address}
                                    <br/>
                                    {contact_email}
                                </p>
                            </Collapse.Panel>
                            <Collapse.Panel header="Registration" key="3">
                                <br/>
                                In order to start your task, please log in with your account. If you do not have an account yet, please click this { }
                                <Button size={"small"} key="login" onClick={ (e) => {
                                    e.preventDefault();
                                    navigate('/login');
                                }
                                }>
                                    Login
                                </Button> { } button.
                                <br/>
                                <br/>
                                <br/>
                                <br/>
                                            <Form
                                                name="basic"
                                                labelCol={{ span: 8 }}
                                                wrapperCol={{ span: 16 }}
                                                style={{ maxWidth: 600 }}
                                                initialValues={{ remember: true }}
                                                onFinish={(x) => onFinish(x, navigate, setToken)}
                                                onFinishFailed={onFinishFailed}
                                                autoComplete="off"
                                            >
                                                <Form.Item<RegistrationFieldType>
                                                    label="Username"
                                                    name="username"
                                                    rules={[{ required: true, message: 'Please input your username!' }, {type: 'string'}]}
                                                >
                                                    <Input />
                                                </Form.Item>

                                                <Form.Item<RegistrationFieldType>
                                                    label="Email"
                                                    name="email"
                                                    rules={[{ required: true, message: 'Please input your email!' }, {type: 'email', message: 'Please enter a valid email!'}]}
                                                    >
                                                    <Input />
                                                </Form.Item>

                                                <Form.Item<RegistrationFieldType>
                                                    label="Password"
                                                    name="password"
                                                    rules={[{ required: true, message: 'Please input your password!' },  { type: 'string', min: 6,  message: 'Password should be longer than 6 characters.' }]}
                                                    >
                                                    <Input.Password />
                                                </Form.Item>

                                                <Form.Item
                                                    name="confirm"
                                                    label="Confirm Password"
                                                    dependencies={['password']}
                                                    hasFeedback
                                                    rules={[
                                                        {
                                                            required: true,
                                                            message: 'Please confirm your password!',
                                                        },
                                                        ({ getFieldValue }) => ({
                                                            validator(_, value) {
                                                                if (!value || getFieldValue('password') === value) {
                                                                    return Promise.resolve();
                                                                }
                                                                return Promise.reject(new Error('The new password that you entered do not match!'));
                                                            },
                                                        }),
                                                    ]}
                                                >
                                                    <Input.Password />
                                                </Form.Item>


                                                <Form.Item
                                                    name="country"
                                                    label="Country of Residence"
                                                    rules={[{ required: true, message: 'Please select your country of residence!' }]}
                                                >
                                                    <Select placeholder="country of residence">
                                                        <Option value="United Kingdom">United Kingdom</Option>
                                                        <Option value="Afghanistan">Afghanistan</Option>
                                                        <Option value="Albania">Albania</Option>
                                                        <Option value="Algeria">Algeria</Option>
                                                        <Option value="Andorra">Andorra</Option>
                                                        <Option value="Angola">Angola</Option>
                                                        <Option value="Antigua and Barbuda">Antigua and Barbuda</Option>
                                                        <Option value="Argentina">Argentina</Option>
                                                        <Option value="Armenia">Armenia</Option>
                                                        <Option value="Australia">Australia</Option>
                                                        <Option value="Austria">Austria</Option>
                                                        <Option value="Azerbaijan">Azerbaijan</Option>
                                                        <Option value="Bahrain">Bahrain</Option>
                                                        <Option value="Bangladesh">Bangladesh</Option>
                                                        <Option value="Barbados">Barbados</Option>
                                                        <Option value="Belarus">Belarus</Option>
                                                        <Option value="Belgium">Belgium</Option>
                                                        <Option value="Belize">Belize</Option>
                                                        <Option value="Benin">Benin</Option>
                                                        <Option value="Bhutan">Bhutan</Option>
                                                        <Option value="Bolivia">Bolivia</Option>
                                                        <Option value="Bosnia and Herzegovina">Bosnia and Herzegovina</Option>
                                                        <Option value="Botswana">Botswana</Option>
                                                        <Option value="Brazil">Brazil</Option>
                                                        <Option value="Brunei">Brunei</Option>
                                                        <Option value="Bulgaria">Bulgaria</Option>
                                                        <Option value="Burkina Faso">Burkina Faso</Option>
                                                        <Option value="Burundi">Burundi</Option>
                                                        <Option value="Cambodia">Cambodia</Option>
                                                        <Option value="Cameroon">Cameroon</Option>
                                                        <Option value="Canada">Canada</Option>
                                                        <Option value="Cape Verde">Cape Verde</Option>
                                                        <Option value="Central African Republic">Central African Republic</Option>
                                                        <Option value="Chad">Chad</Option>
                                                        <Option value="Chile">Chile</Option>
                                                        <Option value="China">China</Option>
                                                        <Option value="Colombia">Colombia</Option>
                                                        <Option value="Comoros">Comoros</Option>
                                                        <Option value="Congo">Congo</Option>
                                                        <Option value="Congo (Democratic Republic)">Congo (Democratic Republic)</Option>
                                                        <Option value="Costa Rica">Costa Rica</Option>
                                                        <Option value="Croatia">Croatia</Option>
                                                        <Option value="Cuba">Cuba</Option>
                                                        <Option value="Cyprus">Cyprus</Option>
                                                        <Option value="Czechia">Czechia</Option>
                                                        <Option value="Denmark">Denmark</Option>
                                                        <Option value="Djibouti">Djibouti</Option>
                                                        <Option value="Dominica">Dominica</Option>
                                                        <Option value="Dominican Republic">Dominican Republic</Option>
                                                        <Option value="East Timor">East Timor</Option>
                                                        <Option value="Ecuador">Ecuador</Option>
                                                        <Option value="Egypt">Egypt</Option>
                                                        <Option value="El Salvador">El Salvador</Option>
                                                        <Option value="Equatorial Guinea">Equatorial Guinea</Option>
                                                        <Option value="Eritrea">Eritrea</Option>
                                                        <Option value="Estonia">Estonia</Option>
                                                        <Option value="Eswatini">Eswatini</Option>
                                                        <Option value="Ethiopia">Ethiopia</Option>
                                                        <Option value="Fiji">Fiji</Option>
                                                        <Option value="Finland">Finland</Option>
                                                        <Option value="France">France</Option>
                                                        <Option value="Gabon">Gabon</Option>
                                                        <Option value="Georgia">Georgia</Option>
                                                        <Option value="Germany">Germany</Option>
                                                        <Option value="Ghana">Ghana</Option>
                                                        <Option value="Greece">Greece</Option>
                                                        <Option value="Grenada">Grenada</Option>
                                                        <Option value="Guatemala">Guatemala</Option>
                                                        <Option value="Guinea">Guinea</Option>
                                                        <Option value="Guinea-Bissau">Guinea-Bissau</Option>
                                                        <Option value="Guyana">Guyana</Option>
                                                        <Option value="Haiti">Haiti</Option>
                                                        <Option value="Honduras">Honduras</Option>
                                                        <Option value="Hungary">Hungary</Option>
                                                        <Option value="Iceland">Iceland</Option>
                                                        <Option value="India">India</Option>
                                                        <Option value="Indonesia">Indonesia</Option>
                                                        <Option value="Iran">Iran</Option>
                                                        <Option value="Iraq">Iraq</Option>
                                                        <Option value="Ireland">Ireland</Option>
                                                        <Option value="Israel">Israel</Option>
                                                        <Option value="Italy">Italy</Option>
                                                        <Option value="Ivory Coast">Ivory Coast</Option>
                                                        <Option value="Jamaica">Jamaica</Option>
                                                        <Option value="Japan">Japan</Option>
                                                        <Option value="Jordan">Jordan</Option>
                                                        <Option value="Kazakhstan">Kazakhstan</Option>
                                                        <Option value="Kenya">Kenya</Option>
                                                        <Option value="Kiribati">Kiribati</Option>
                                                        <Option value="Kosovo">Kosovo</Option>
                                                        <Option value="Kuwait">Kuwait</Option>
                                                        <Option value="Kyrgyzstan">Kyrgyzstan</Option>
                                                        <Option value="Laos">Laos</Option>
                                                        <Option value="Latvia">Latvia</Option>
                                                        <Option value="Lebanon">Lebanon</Option>
                                                        <Option value="Lesotho">Lesotho</Option>
                                                        <Option value="Liberia">Liberia</Option>
                                                        <Option value="Libya">Libya</Option>
                                                        <Option value="Liechtenstein">Liechtenstein</Option>
                                                        <Option value="Lithuania">Lithuania</Option>
                                                        <Option value="Luxembourg">Luxembourg</Option>
                                                        <Option value="Madagascar">Madagascar</Option>
                                                        <Option value="Malawi">Malawi</Option>
                                                        <Option value="Malaysia">Malaysia</Option>
                                                        <Option value="Maldives">Maldives</Option>
                                                        <Option value="Mali">Mali</Option>
                                                        <Option value="Malta">Malta</Option>
                                                        <Option value="Marshall Islands">Marshall Islands</Option>
                                                        <Option value="Mauritania">Mauritania</Option>
                                                        <Option value="Mauritius">Mauritius</Option>
                                                        <Option value="Mexico">Mexico</Option>
                                                        <Option value="Micronesia">Micronesia</Option>
                                                        <Option value="Moldova">Moldova</Option>
                                                        <Option value="Monaco">Monaco</Option>
                                                        <Option value="Mongolia">Mongolia</Option>
                                                        <Option value="Montenegro">Montenegro</Option>
                                                        <Option value="Morocco">Morocco</Option>
                                                        <Option value="Mozambique">Mozambique</Option>
                                                        <Option value="Myanmar (Burma)">Myanmar (Burma)</Option>
                                                        <Option value="Namibia">Namibia</Option>
                                                        <Option value="Nauru">Nauru</Option>
                                                        <Option value="Nepal">Nepal</Option>
                                                        <Option value="Netherlands">Netherlands</Option>
                                                        <Option value="New Zealand">New Zealand</Option>
                                                        <Option value="Nicaragua">Nicaragua</Option>
                                                        <Option value="Niger">Niger</Option>
                                                        <Option value="Nigeria">Nigeria</Option>
                                                        <Option value="North Korea">North Korea</Option>
                                                        <Option value="North Macedonia">North Macedonia</Option>
                                                        <Option value="Norway">Norway</Option>
                                                        <Option value="Oman">Oman</Option>
                                                        <Option value="Pakistan">Pakistan</Option>
                                                        <Option value="Palau">Palau</Option>
                                                        <Option value="Panama">Panama</Option>
                                                        <Option value="Papua New Guinea">Papua New Guinea</Option>
                                                        <Option value="Paraguay">Paraguay</Option>
                                                        <Option value="Peru">Peru</Option>
                                                        <Option value="Philippines">Philippines</Option>
                                                        <Option value="Poland">Poland</Option>
                                                        <Option value="Portugal">Portugal</Option>
                                                        <Option value="Qatar">Qatar</Option>
                                                        <Option value="Romania">Romania</Option>
                                                        <Option value="Russia">Russia</Option>
                                                        <Option value="Rwanda">Rwanda</Option>
                                                        <Option value="Samoa">Samoa</Option>
                                                        <Option value="San Marino">San Marino</Option>
                                                        <Option value="Sao Tome and Principe">Sao Tome and Principe</Option>
                                                        <Option value="Saudi Arabia">Saudi Arabia</Option>
                                                        <Option value="Senegal">Senegal</Option>
                                                        <Option value="Serbia">Serbia</Option>
                                                        <Option value="Seychelles">Seychelles</Option>
                                                        <Option value="Sierra Leone">Sierra Leone</Option>
                                                        <Option value="Singapore">Singapore</Option>
                                                        <Option value="Slovakia">Slovakia</Option>
                                                        <Option value="Slovenia">Slovenia</Option>
                                                        <Option value="Solomon Islands">Solomon Islands</Option>
                                                        <Option value="Somalia">Somalia</Option>
                                                        <Option value="South Africa">South Africa</Option>
                                                        <Option value="South Korea">South Korea</Option>
                                                        <Option value="South Sudan">South Sudan</Option>
                                                        <Option value="Spain">Spain</Option>
                                                        <Option value="Sri Lanka">Sri Lanka</Option>
                                                        <Option value="St Kitts and Nevis">St Kitts and Nevis</Option>
                                                        <Option value="St Lucia">St Lucia</Option>
                                                        <Option value="St Vincent">St Vincent</Option>
                                                        <Option value="Sudan">Sudan</Option>
                                                        <Option value="Suriname">Suriname</Option>
                                                        <Option value="Sweden">Sweden</Option>
                                                        <Option value="Switzerland">Switzerland</Option>
                                                        <Option value="Syria">Syria</Option>
                                                        <Option value="Tajikistan">Tajikistan</Option>
                                                        <Option value="Tanzania">Tanzania</Option>
                                                        <Option value="Thailand">Thailand</Option>
                                                        <Option value="The Bahamas">The Bahamas</Option>
                                                        <Option value="The Gambia">The Gambia</Option>
                                                        <Option value="Togo">Togo</Option>
                                                        <Option value="Tonga">Tonga</Option>
                                                        <Option value="Trinidad and Tobago">Trinidad and Tobago</Option>
                                                        <Option value="Tunisia">Tunisia</Option>
                                                        <Option value="Turkey">Turkey</Option>
                                                        <Option value="Turkmenistan">Turkmenistan</Option>
                                                        <Option value="Tuvalu">Tuvalu</Option>
                                                        <Option value="Uganda">Uganda</Option>
                                                        <Option value="Ukraine">Ukraine</Option>
                                                        <Option value="United Arab Emirates">United Arab Emirates</Option>
                                                        <Option value="United States">United States</Option>
                                                        <Option value="Uruguay">Uruguay</Option>
                                                        <Option value="Uzbekistan">Uzbekistan</Option>
                                                        <Option value="Vanuatu">Vanuatu</Option>
                                                        <Option value="Vatican City">Vatican City</Option>
                                                        <Option value="Venezuela">Venezuela</Option>
                                                        <Option value="Vietnam">Vietnam</Option>
                                                        <Option value="Yemen">Yemen</Option>
                                                        <Option value="Zambia">Zambia</Option>
                                                        <Option value="Zimbabwe">Zimbabwe</Option>
                                                    </Select>
                                                </Form.Item>

                                    <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                        <Button type="primary" htmlType="submit">
                                            Submit
                                        </Button>
                                    </Form.Item>
                                </Form>

                            </Collapse.Panel>
                        </Collapse>

                    </div>

                </Content>
                <Footer style={{ textAlign: 'center', backgroundColor:'#F5F5F5FF' }}>Cambridge LTL ©2023</Footer>
            </Layout>
        )
}

export default Register;
