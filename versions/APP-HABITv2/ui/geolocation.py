from __future__ import annotations

import streamlit as st


_geo_component = st.components.v2.component(
    "app_habit_geolocation",

    html="""
    <div class="geo-box">
        <div class="geo-copy">
            <strong>Météo locale</strong>
            <span>Votre position permet d'adapter la tenue à la météo.</span>
        </div>

        <button id="geo-button">
            Autoriser ma position
        </button>

        <button id="geo-skip" class="secondary">
            Plus tard
        </button>
    </div>
    """,

    css="""
    .geo-box {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 12px;

        padding: 14px 16px;

        border: 1px solid #DEDAD1;
        border-radius: 18px;

        background: rgba(255,255,255,.42);

        box-sizing: border-box;
    }

    .geo-copy {
        flex: 1;

        display: flex;
        flex-direction: column;
        gap: 2px;

        color: #111;
    }

    .geo-copy strong {
        font-size: 14px;
        font-weight: 750;
    }

    .geo-copy span {
        font-size: 12px;
        color: #74716A;
    }

    button {
        border: 0;
        border-radius: 999px;

        padding: 10px 16px;

        cursor: pointer;

        font-size: 12px;
        font-weight: 700;

        white-space: nowrap;

        background: #111;
        color: #fff;
    }

    button.secondary {
        background: transparent;
        color: #111;
        border: 1px solid #DEDAD1;
    }

    button:disabled {
        opacity: .55;
        cursor: default;
    }

    @media (max-width: 650px) {
        .geo-box {
            flex-direction: column;
            align-items: stretch;
        }

        button {
            width: 100%;
        }
    }
    """,

    js="""
    export default function(component) {

        const {
            parentElement,
            setStateValue
        } = component;

        const button =
            parentElement.querySelector("#geo-button");

        const skip =
            parentElement.querySelector("#geo-skip");

        if (!button || !skip) {
            return;
        }


        button.onclick = () => {

            if (!navigator.geolocation) {

                setStateValue("location", {
                    status: "unsupported"
                });

                return;
            }


            button.disabled = true;
            button.textContent = "Localisation…";


            navigator.geolocation.getCurrentPosition(

                (position) => {

                    setStateValue("location", {
                        status: "success",
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });

                },

                (error) => {

                    setStateValue("location", {
                        status: "error",
                        code: error.code,
                        message: error.message
                    });

                    button.disabled = false;
                    button.textContent = "Autoriser ma position";

                },

                {
                    enableHighAccuracy: false,
                    timeout: 10000,
                    maximumAge: 900000
                }
            );
        };


        skip.onclick = () => {

            setStateValue("location", {
                status: "skipped"
            });

        };
    }
    """
)


def request_location(key="app_habit_location"):

    def on_location_change():
        pass

    result = _geo_component(
        key=key,

        default={
            "location": None
        },

        on_location_change=on_location_change,
    )

    location = getattr(
        result,
        "location",
        None
    )

    return location
