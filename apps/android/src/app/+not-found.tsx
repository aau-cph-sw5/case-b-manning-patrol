import {Link} from 'expo-router';
import { StackScreen } from 'expo-router/build/layouts/stack-utils';
import { StyleSheet, View } from 'react-native';

export default function NotFoundScreen () {
    return (
        <>
            <StackScreen options={{title: 'Ups! Side ikke fundet'}} />
            <View style={styles.container}>
                <Link href={'/'} style={styles.button}>
                    Gå tilbage til Hjemmeside!
                </Link>
            </View>
        </>
    )
}

const styles = StyleSheet.create ({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        justifyContent: 'center',
        alignItems: 'center'
    },

    button: {
        fontSize: 20,
        textDecorationLine: 'underline',
        color: '#25292e'
    }
})