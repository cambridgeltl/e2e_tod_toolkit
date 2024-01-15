// TokenService.tsx
// ----------------------------------------------------------------------------------------
// Description: This hook is used for managing JWT tokens in the application.
//              It provides functions to save, retrieve, remove, and decode JWT tokens
//              stored in the session storage. Additionally, it handles extracting user
//              roles and permissions from the token.
// Author: Xiaobin Wang and Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import { SetStateAction, useState} from 'react';
import { jwtDecode } from 'jwt-decode';
import { JwtPayload } from "jwt-decode";

// Extending the JwtPayload to include custom fields like role
interface CustomTokenPayload extends JwtPayload {
    role: {name:string; permissions:string[]};
}

function useToken() {

    // Retrieves the token from session storage
    function getToken() {
        const userToken = sessionStorage.getItem('token');
        return userToken && userToken
    }

    // State to hold the token
    const [token, setToken] = useState(getToken());

    // Saves a user token to session storage and updates the state
    function saveToken(userToken: SetStateAction<string | null>) {
        if (typeof userToken === "string") {
            sessionStorage.setItem('token', userToken);
        }
        setToken(userToken);
    }

    // Extracts and returns the user role from the token
    function getUserRole(): string {
        try {
            if (token) {
                const decoded: CustomTokenPayload = jwtDecode<CustomTokenPayload>(token);
                return decoded.role.name;
            } else {
                console.log("Token is null or undefined");
                return '';
            }
        } catch (error) {
            console.error("Error decoding token:", error);
            return '';
        }
    }


    // Extracts and returns user permissions from the token
    function getUserPermissions(): string[] {
        try {
            if (token) {
                const decoded: CustomTokenPayload = jwtDecode<CustomTokenPayload>(token);
                return decoded.role.permissions;
            } else {
                console.log("Token is null or undefined");
                return [];
            }
        } catch (error) {
            console.error("Error decoding token:", error);
            return [];
        }
    }

    // Removes the token from session storage and updates the state
    function removeToken() {
        sessionStorage.removeItem("token");
        setToken(null);
    }

    // Public API of the hook
    return {
        setToken: saveToken,
        token,
        removeToken,
        getUserRole,
        getToken,
        getUserPermissions,
    }

}

export default useToken;
